from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from assertions import assert_forbidden, json_body
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo


def signup_payload(**overrides):
    suffix = uuid4().hex[:10]
    payload = {
        "nome": "Novo Usuario Cadastro",
        "email": f"cadastro-{suffix}@belloalimentos.com.br",
        "cargo": "Vendedor",
        "superior": "Coordenador Teste",
        "veiculo_placa": f"C{suffix[:6]}",
        "veiculo_modelo": "honda/hrv",
        "veiculo_marca": "honda",
        "observacao": "Cadastro criado por teste.",
    }
    payload.update(overrides)
    return payload


def admin_headers(db) -> tuple[dict[str, str], Usuario]:
    settings = get_settings()
    admin = Usuario(
        nome="Admin Cadastro Teste",
        email=f"admin-cadastro-{uuid4().hex}@bello.local",
        senha_hash=hash_password("senha-admin-teste"),
        perfil=PerfilUsuario.admin,
    )
    db.add(admin)
    db.commit()
    token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
    return {"Authorization": f"Bearer {token}"}, admin


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-019", "RNF-004"))
def test_solicitacao_cadastro_publica_cria_registro_pendente(api_client):
    payload = signup_payload()

    response = api_client.post("/signup-requests", json=payload)

    assert response.status_code == 201, response.text
    data = json_body(response)
    assert data["status"] == "pendente"
    assert data["email"] == payload["email"]
    assert data["veiculo_placa"] == payload["veiculo_placa"].upper()
    assert data["veiculo_modelo"] == "HRV"
    assert data["veiculo_marca"] == "HONDA"


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-019", "RNF-004"))
def test_motorista_nao_lista_solicitacoes_cadastro(api_client, motorista_auth_headers):
    response = api_client.get("/signup-requests", headers=motorista_auth_headers)

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-019", "RNF-004"))
def test_admin_aprova_solicitacao_e_cria_usuario_e_veiculo(api_client):
    db = SessionLocal()
    headers, admin = admin_headers(db)
    payload = signup_payload()
    created_user_id = None
    created_vehicle_id = None
    try:
        create_response = api_client.post("/signup-requests", json=payload)
        assert create_response.status_code == 201, create_response.text
        solicitacao_id = json_body(create_response)["id"]

        approve_response = api_client.post(
            f"/signup-requests/{solicitacao_id}/approve",
            headers=headers,
            json={
                "senha_temporaria": "senha-temporaria-teste",
                "perfil": "motorista",
                "superior_id": None,
                "pode_aprovar": False,
                "tipo_veiculo": "proprio",
            },
        )

        assert approve_response.status_code == 200, approve_response.text
        data = json_body(approve_response)
        assert data["status"] == "aprovada"
        created_user_id = data["usuario_id"]
        created_vehicle_id = data["veiculo_id"]

        login_response = api_client.post(
            "/auth/login",
            json={"email": payload["email"], "senha": "senha-temporaria-teste"},
        )
        assert login_response.status_code == 200, login_response.text

        veiculo = db.scalar(select(Veiculo).where(Veiculo.placa == payload["veiculo_placa"].upper()))
        assert veiculo is not None
        assert veiculo.modelo == "HRV"
        assert veiculo.marca == "HONDA"
    finally:
        db.rollback()
        for model, item_id in ((Veiculo, created_vehicle_id), (Usuario, created_user_id), (Usuario, admin.id)):
            if item_id:
                persisted = db.get(model, item_id)
                if persisted is not None:
                    db.delete(persisted)
        db.commit()
        db.close()
