from uuid import uuid4

import pytest

from assertions import assert_forbidden, response_items
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-016", "RN-031"))
def test_admin_lista_equipe_completa(api_client):
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Equipe Teste",
            email=f"admin.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        fora_da_cadeia = Usuario(
            nome="Motorista Fora Da Cadeia",
            email=f"motorista.fora.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([admin, fora_da_cadeia])
        db.commit()
        created.extend([admin, fora_da_cadeia])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.get("/users/equipe", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        ids = {item["id"] for item in response_items(response)}
        assert str(admin.id) in ids
        assert str(fora_da_cadeia.id) in ids
        for item in response_items(response):
            assert set(item.keys()) == {"id", "nome", "cargo"}
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-016", "RN-031"))
def test_supervisor_lista_apenas_propria_cadeia(api_client):
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        gerente = Usuario(
            nome="Gerente Equipe Teste",
            email=f"gerente.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="GERENTE",
            pode_aprovar=True,
        )
        db.add(gerente)
        db.flush()

        coordenador_local = Usuario(
            nome="Coordenador Equipe Teste",
            email=f"coordenador.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="COORDENADOR LOCAL",
            pode_aprovar=True,
            superior_id=gerente.id,
        )
        db.add(coordenador_local)
        db.flush()

        motorista_subordinado = Usuario(
            nome="Motorista Subordinado Equipe Teste",
            email=f"motorista.subordinado.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            cargo="MOTORISTA",
            superior_id=coordenador_local.id,
        )
        fora_da_cadeia = Usuario(
            nome="Motorista Fora Da Cadeia Equipe Teste",
            email=f"motorista.fora.cadeia.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([motorista_subordinado, fora_da_cadeia])
        db.commit()
        created.extend([gerente, coordenador_local, motorista_subordinado, fora_da_cadeia])

        token = create_access_token(str(gerente.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.get("/users/equipe", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        items = response_items(response)
        ids = {item["id"] for item in items}
        assert ids == {str(gerente.id), str(coordenador_local.id), str(motorista_subordinado.id)}
        assert str(fora_da_cadeia.id) not in ids

        coordenador_item = next(item for item in items if item["id"] == str(coordenador_local.id))
        assert coordenador_item["cargo"] == "COORDENADOR LOCAL"
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RNF-004"))
def test_motorista_nao_lista_equipe(api_client, motorista_auth_headers):
    response = api_client.get("/users/equipe", headers=motorista_auth_headers)

    assert_forbidden(response)
