"""Troca do veiculo de viagem concluida pelo administrador (RF-024, RN-040)."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete

from assertions import assert_business_rule_violation, assert_forbidden, json_body
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from helpers import create_trip_in_progress, create_trip_ready_for_monthly_closure


def _auth_headers(usuario_id) -> dict[str, str]:
    settings = get_settings()
    token = create_access_token(str(usuario_id), settings.secret_key, settings.access_token_expire_minutes)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def troca_veiculo_ctx():
    """Admin descartavel e um segundo veiculo (alocado) para receber a viagem."""
    db = SessionLocal()
    sufixo = uuid4().hex[:6].upper()
    admin = Usuario(
        nome="Admin Troca Veiculo Teste",
        email=f"admin.troca.{uuid4().hex}@bello.local",
        senha_hash="hash",
        perfil=PerfilUsuario.admin,
    )
    veiculo = Veiculo(
        placa=f"TV{sufixo}"[:10],
        modelo="ONIX",
        tipo=TipoVeiculo.empresa,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
    )
    db.add_all([admin, veiculo])
    db.commit()
    try:
        yield {
            "admin_id": admin.id,
            "admin_headers": _auth_headers(admin.id),
            "veiculo_id": veiculo.id,
            "veiculo_placa": veiculo.placa,
        }
    finally:
        db.execute(delete(Viagem).where(Viagem.veiculo_id == veiculo.id))
        db.execute(delete(Viagem).where(Viagem.usuario_id == admin.id))
        db.execute(delete(Veiculo).where(Veiculo.id == veiculo.id))
        db.execute(delete(Usuario).where(Usuario.id == admin.id))
        db.commit()
        db.close()


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-024", "RN-040"))
def test_admin_troca_veiculo_de_viagem_concluida(
    api_client, motorista_auth_headers, test_vehicle_id, troca_veiculo_ctx
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.patch(
        f"/trips/{trip['id']}",
        json={"veiculo_id": str(troca_veiculo_ctx["veiculo_id"])},
        headers=troca_veiculo_ctx["admin_headers"],
    )

    assert response.status_code == 200, response.text
    data = json_body(response)
    assert data["veiculo_id"] == str(troca_veiculo_ctx["veiculo_id"])
    assert data["veiculo_placa"] == troca_veiculo_ctx["veiculo_placa"]
    assert float(data["km_rodado"]) == pytest.approx(float(trip["km_rodado"]))


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-024", "RN-040"))
def test_superior_nao_pode_trocar_veiculo_da_viagem(
    api_client, motorista_auth_headers, aprovador_auth_headers, test_vehicle_id, troca_veiculo_ctx
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.patch(
        f"/trips/{trip['id']}",
        json={"veiculo_id": str(troca_veiculo_ctx["veiculo_id"])},
        headers=aprovador_auth_headers,
    )

    assert_forbidden(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="viagem", referencias=("RF-024", "RN-040"))
def test_troca_de_veiculo_bloqueada_em_viagem_em_andamento(
    api_client, motorista_auth_headers, test_vehicle_id, troca_veiculo_ctx
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.patch(
        f"/trips/{trip['id']}",
        json={"veiculo_id": str(troca_veiculo_ctx["veiculo_id"])},
        headers=troca_veiculo_ctx["admin_headers"],
    )

    assert_business_rule_violation(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="viagem", referencias=("RF-024", "RN-040"))
def test_troca_para_veiculo_com_viagem_no_mesmo_horario_e_bloqueada(
    api_client, motorista_auth_headers, test_vehicle_id, troca_veiculo_ctx
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    db = SessionLocal()
    try:
        viagem = db.get(Viagem, UUID(trip["id"]))
        db.add(
            Viagem(
                usuario_id=troca_veiculo_ctx["admin_id"],
                veiculo_id=troca_veiculo_ctx["veiculo_id"],
                status=StatusViagem.concluida,
                km_inicial=500,
                km_final=520,
                km_rodado=20,
                rota_utilizada="Viagem concorrente",
                partida_em=viagem.partida_em - timedelta(minutes=30),
                chegada_em=viagem.chegada_em + timedelta(minutes=30),
            )
        )
        db.commit()
    finally:
        db.close()

    response = api_client.patch(
        f"/trips/{trip['id']}",
        json={"veiculo_id": str(troca_veiculo_ctx["veiculo_id"])},
        headers=troca_veiculo_ctx["admin_headers"],
    )

    assert_business_rule_violation(response)
    assert troca_veiculo_ctx["veiculo_placa"] in json_body(response)["detail"]
