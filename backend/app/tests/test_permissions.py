from uuid import uuid4

import pytest

from assertions import assert_forbidden, assert_unauthorized, response_items
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from factories import start_payload
from helpers import create_trip_in_progress, create_trip_ready_for_monthly_closure, post_trip_start


def monthly_params() -> dict[str, int]:
    from datetime import date

    today = date.today()
    return {"ano": today.year, "mes": today.month}


@pytest.mark.permissao
@pytest.mark.autenticacao
@pytest.mark.risco(peso=100, criticidade="critica", area="autenticacao", referencias=("RN-001", "RNF-002"))
def test_usuario_sem_token_nao_lista_viagens(api_client):
    response = api_client.get("/trips")

    assert_unauthorized(response)


@pytest.mark.permissao
@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-013", "RNF-004"))
def test_motorista_lista_proprias_viagens(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get("/trips", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    trips = response_items(response)
    assert any(str(item.get("id") or item.get("viagem_id")) == trip["id"] for item in trips)


@pytest.mark.permissao
@pytest.mark.aprovacao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-014", "RNF-004"))
def test_motorista_nao_fecha_fechamento_mensal(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.post(
        f"/reports/monthly/closures/{trip['usuario_id']}/close",
        params=monthly_params(),
        json={},
        headers=motorista_auth_headers,
    )

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-004", "RNF-004"))
def test_analista_nao_inicia_viagem(api_client, analista_auth_headers, test_vehicle_id):
    response = post_trip_start(api_client, analista_auth_headers, start_payload(test_vehicle_id))

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-004", "RN-026", "RNF-004"))
def test_admin_nao_inicia_viagem(api_client, test_vehicle_id):
    settings = get_settings()
    db = SessionLocal()
    admin_id = None
    try:
        admin = Usuario(
            nome="Admin Sem Viagem Teste",
            email=f"admin.sem.viagem.{uuid4().hex}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
            cargo="Administrador",
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id

        token = create_access_token(str(admin_id), settings.secret_key, settings.access_token_expire_minutes)
        response = post_trip_start(
            api_client,
            {"Authorization": f"Bearer {token}"},
            start_payload(test_vehicle_id),
        )

        assert_forbidden(response)
    finally:
        if admin_id is not None:
            persisted = db.get(Usuario, admin_id)
            if persisted is not None:
                db.delete(persisted)
                db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RNF-004",))
def test_analista_nao_cadastra_veiculo(api_client, analista_auth_headers):
    response = api_client.post(
        "/vehicles",
        json={
            "placa": "TST1234",
            "modelo": "Veiculo Teste",
            "tipo": "empresa",
            "ativo": True,
        },
        headers=analista_auth_headers,
    )

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-013", "RNF-004"))
def test_supervisor_sem_poder_de_aprovacao_lista_somente_proprias_viagens(api_client):
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        supervisor = Usuario(
            nome="Supervisor Sem Aprovacao Teste",
            email="supervisor.sem.aprovacao.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="Supervisor",
            pode_aprovar=False,
        )
        outro_usuario = Usuario(
            nome="Outro Motorista Permissao Teste",
            email="outro.motorista.permissao.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([supervisor, outro_usuario])
        db.flush()
        created.extend([supervisor, outro_usuario])

        veiculo_supervisor = Veiculo(
            placa="SUP1T01",
            modelo="Veiculo Supervisor",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=supervisor.id,
        )
        veiculo_outro = Veiculo(
            placa="OUT1T01",
            modelo="Veiculo Outro",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=outro_usuario.id,
        )
        db.add_all([veiculo_supervisor, veiculo_outro])
        db.flush()
        created.extend([veiculo_supervisor, veiculo_outro])

        viagem_supervisor = Viagem(
            usuario_id=supervisor.id,
            veiculo_id=veiculo_supervisor.id,
            status=StatusViagem.em_andamento,
            km_inicial=10,
        )
        viagem_outro = Viagem(
            usuario_id=outro_usuario.id,
            veiculo_id=veiculo_outro.id,
            status=StatusViagem.em_andamento,
            km_inicial=20,
        )
        db.add_all([viagem_supervisor, viagem_outro])
        db.commit()
        created.extend([viagem_supervisor, viagem_outro])

        token = create_access_token(str(supervisor.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.get("/trips", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        trip_ids = {item["id"] for item in response_items(response)}
        assert str(viagem_supervisor.id) in trip_ids
        assert str(viagem_outro.id) not in trip_ids
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()
