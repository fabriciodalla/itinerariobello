from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assertions import (
    assert_business_rule_violation,
    assert_forbidden,
    assert_validation_error,
    json_body,
    response_items,
)
from sqlalchemy import delete, or_

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario
from app.models.fechamento_mensal import FechamentoMensal
from app.models.usuario import Usuario
from app.models.viagem import Viagem
from helpers import create_trip_in_progress, create_trip_ready_for_monthly_closure


def monthly_params() -> dict[str, int]:
    today = date.today()
    return {"ano": today.year, "mes": today.month}


def _auth_headers(usuario_id) -> dict[str, str]:
    settings = get_settings()
    token = create_access_token(str(usuario_id), settings.secret_key, settings.access_token_expire_minutes)
    return {"Authorization": f"Bearer {token}"}


def manual_payload(motorista_id, veiculo_id, **overrides):
    partida = datetime.now(timezone.utc) - timedelta(hours=3)
    chegada = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {
        "usuario_id": str(motorista_id),
        "veiculo_id": str(veiculo_id),
        "km_inicial": 1000.0,
        "km_final": 1050.0,
        "rota_utilizada": "Cliente X -> Cliente Y",
        "partida_em": partida.isoformat(),
        "chegada_em": chegada.isoformat(),
        "motivo_manual": "Motorista sem acesso ao app no dia; lancamento retroativo pelo administrador.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def aprovador_id(aprovador_auth_headers):
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter_by(email=os.environ["TEST_APROVADOR_EMAIL"]).first()
        assert usuario is not None, "Usuario aprovador de teste nao encontrado."
        return usuario.id
    finally:
        db.close()


@pytest.fixture
def manual_trip_actors(aprovador_id):
    """Cria admin e motorista descartaveis para os testes de lancamento manual
    (RF-023, RN-036 a RN-039), com o motorista subordinado ao aprovador de
    teste, necessario para o cenario de fechamento mensal ja fechado."""
    db = SessionLocal()
    created: list[Usuario] = []
    try:
        admin = Usuario(
            nome="Admin Lancamento Manual Teste",
            email=f"admin.manual.{uuid4().hex}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        motorista = Usuario(
            nome="Motorista Lancamento Manual Teste",
            email=f"motorista.manual.{uuid4().hex}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            superior_id=aprovador_id,
        )
        db.add_all([admin, motorista])
        db.commit()
        created.extend([admin, motorista])

        yield {
            "admin_id": admin.id,
            "admin_headers": _auth_headers(admin.id),
            "motorista_id": motorista.id,
            "motorista_headers": _auth_headers(motorista.id),
        }
    finally:
        usuario_ids = [item.id for item in created]
        db.execute(
            delete(Viagem).where(
                or_(Viagem.usuario_id.in_(usuario_ids), Viagem.criado_por_id.in_(usuario_ids))
            )
        )
        db.execute(
            delete(FechamentoMensal).where(
                or_(
                    FechamentoMensal.motorista_id.in_(usuario_ids),
                    FechamentoMensal.superior_id.in_(usuario_ids),
                )
            )
        )
        for item in reversed(created):
            persisted = db.get(Usuario, item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-023", "RN-036", "RN-037"))
def test_admin_lanca_viagem_manual_sem_foto_e_gps(api_client, manual_trip_actors, test_vehicle_id):
    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id)

    response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])

    assert response.status_code == 201, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["status"] == "concluida"
    assert data["origem_registro"] == "manual"
    assert data["motivo_manual"] == payload["motivo_manual"]
    assert data["foto_hodometro_inicial"] is None
    assert data["foto_hodometro_final"] is None
    assert str(data["usuario_id"]) == str(manual_trip_actors["motorista_id"])
    assert float(data["km_rodado"]) == payload["km_final"] - payload["km_inicial"]


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-023", "RN-036"))
def test_motorista_nao_lanca_viagem_manual(api_client, motorista_auth_headers, manual_trip_actors, test_vehicle_id):
    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id)

    response = api_client.post("/trips/manual", json=payload, headers=motorista_auth_headers)

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-023", "RN-036"))
def test_aprovador_nao_lanca_viagem_manual(api_client, aprovador_auth_headers, manual_trip_actors, test_vehicle_id):
    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id)

    response = api_client.post("/trips/manual", json=payload, headers=aprovador_auth_headers)

    assert_forbidden(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-023", "RN-037"))
def test_viagem_manual_sem_motivo_retorna_erro(api_client, manual_trip_actors, test_vehicle_id):
    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id)
    payload.pop("motivo_manual")

    response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])

    assert_validation_error(response)


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-023", "RN-011"))
def test_viagem_manual_km_final_menor_que_inicial_retorna_erro(api_client, manual_trip_actors, test_vehicle_id):
    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id, km_final=900.0)

    response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])

    assert_business_rule_violation(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="viagem", referencias=("RF-023", "RN-038", "RN-018"))
def test_viagem_manual_bloqueada_quando_veiculo_ja_em_uso_no_dia(
    api_client,
    motorista_auth_headers,
    manual_trip_actors,
    test_vehicle_id,
):
    create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    payload = manual_payload(manual_trip_actors["motorista_id"], test_vehicle_id)
    response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])

    assert_business_rule_violation(response)


@pytest.mark.aprovacao
@pytest.mark.risco(peso=50, criticidade="alta", area="aprovacao", referencias=("RF-023", "RN-039"))
def test_viagem_manual_bloqueada_quando_fechamento_mensal_fechado(
    api_client,
    aprovador_auth_headers,
    manual_trip_actors,
    test_vehicle_id,
):
    motorista_id = manual_trip_actors["motorista_id"]
    create_trip_ready_for_monthly_closure(api_client, manual_trip_actors["motorista_headers"], test_vehicle_id)

    close_response = api_client.post(
        f"/reports/monthly/closures/{motorista_id}/close",
        params=monthly_params(),
        json={},
        headers=aprovador_auth_headers,
    )
    assert close_response.status_code == 200, close_response.text

    payload = manual_payload(motorista_id, test_vehicle_id)
    response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])

    assert_business_rule_violation(response)


@pytest.mark.relatorio
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-023", "RN-037"))
def test_relatorio_mensal_exibe_viagem_manual_com_motivo(
    api_client,
    aprovador_auth_headers,
    manual_trip_actors,
    test_vehicle_id,
):
    motorista_id = manual_trip_actors["motorista_id"]
    payload = manual_payload(motorista_id, test_vehicle_id)

    create_response = api_client.post("/trips/manual", json=payload, headers=manual_trip_actors["admin_headers"])
    assert create_response.status_code == 201, create_response.text

    response = api_client.get(
        "/reports/monthly",
        params={**monthly_params(), "motorista_id": str(motorista_id)},
        headers=aprovador_auth_headers,
    )
    assert response.status_code == 200, response.text
    items = response_items(response)
    assert len(items) == 1
    assert items[0]["origem_registro"] == "manual"
    assert items[0]["motivo_manual"] == payload["motivo_manual"]
