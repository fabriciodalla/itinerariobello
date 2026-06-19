from datetime import datetime, timezone

import pytest

from assertions import assert_unauthorized, response_items
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from app.services.veiculos import listar_veiculos_disponiveis_para_partida


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-016", "RN-018"),
)
def test_veiculos_disponiveis_ocultam_proprio_de_outro_usuario_e_bloqueiam_viagem_do_dia():
    db = SessionLocal()
    data_referencia = datetime(2026, 5, 14, tzinfo=timezone.utc).date()

    try:
        usuario = Usuario(
            nome="Usuario Teste",
            email="usuario.veiculo.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        outro_usuario = Usuario(
            nome="Outro Usuario",
            email="outro.veiculo.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([usuario, outro_usuario])
        db.flush()

        proprio_do_usuario = Veiculo(
            placa="AAA1A11",
            modelo="Modelo Proprio",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=usuario.id,
        )
        proprio_de_outro = Veiculo(
            placa="BBB2B22",
            modelo="Modelo Outro",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=outro_usuario.id,
        )
        empresa_livre = Veiculo(
            placa="CCC3C33",
            modelo="Modelo Empresa Livre",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
            usuario_responsavel_id=outro_usuario.id,
        )
        empresa_bloqueado = Veiculo(
            placa="DDD4D44",
            modelo="Modelo Empresa Bloqueado",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
            usuario_responsavel_id=outro_usuario.id,
        )
        db.add_all([proprio_do_usuario, proprio_de_outro, empresa_livre, empresa_bloqueado])
        db.flush()

        db.add(
            Viagem(
                usuario_id=outro_usuario.id,
                veiculo_id=empresa_bloqueado.id,
                status=StatusViagem.em_andamento,
                km_inicial=100,
                partida_em=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc),
            )
        )
        db.flush()

        disponiveis = listar_veiculos_disponiveis_para_partida(db, usuario.id, data_referencia)
        ids_disponiveis = [veiculo.id for veiculo in disponiveis]

        assert ids_disponiveis[0] == proprio_do_usuario.id
        assert empresa_livre.id in ids_disponiveis
        assert proprio_de_outro.id not in ids_disponiveis
        assert empresa_bloqueado.id not in ids_disponiveis
    finally:
        db.rollback()
        db.close()


@pytest.mark.autenticacao
@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-016", "RN-018"),
)
def test_endpoint_lista_veiculos_disponiveis_para_usuario_logado(api_client, motorista_auth_headers):
    response = api_client.get("/vehicles", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    veiculos = response_items(response)
    for veiculo in veiculos:
        assert veiculo.get("id")
        assert veiculo.get("placa")
        assert veiculo.get("modelo")
        assert veiculo.get("tipo") in {"proprio", "empresa", "alugado"}
        assert veiculo.get("tipo_disponibilidade") in {"fixo", "alocado"}


@pytest.mark.autenticacao
@pytest.mark.risco(
    peso=100,
    criticidade="critica",
    area="autenticacao",
    referencias=("RF-004", "RN-001", "RNF-002"),
)
def test_endpoint_veiculos_sem_token_retorna_401(api_client):
    response = api_client.get("/vehicles")

    assert_unauthorized(response)
