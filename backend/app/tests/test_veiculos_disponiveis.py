from datetime import date, datetime, timezone

import pytest

from assertions import assert_unauthorized, response_items
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from app.services.veiculos import (
    listar_veiculos_disponiveis_para_partida,
    normalizar_marca_veiculo,
    normalizar_modelo_veiculo,
)
from helpers import create_trip_in_progress


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


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-018"),
)
def test_veiculos_disponiveis_bloqueio_do_dia_usa_fuso_horario_local():
    """O bloqueio de reuso 'no mesmo dia' (RN-018) deve considerar o dia no
    fuso horario do negocio (America/Cuiaba, UTC-4), nao o dia em UTC.

    Uma viagem feita as 22h de 14/05 no horario de Cuiaba vira 02h de 15/05
    em UTC — em UTC ela "parece" ter acontecido no dia de referencia
    (15/05), mas no horario local foi no dia anterior e por isso nao pode
    bloquear o veiculo para uma nova partida no dia local seguinte."""
    db = SessionLocal()
    hoje_local = date(2026, 5, 15)

    try:
        usuario = Usuario(
            nome="Usuario Fuso Teste",
            email="usuario.fuso.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add(usuario)
        db.flush()

        veiculo = Veiculo(
            placa="FFF5F55",
            modelo="Modelo Fuso",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=usuario.id,
        )
        db.add(veiculo)
        db.flush()

        db.add(
            Viagem(
                usuario_id=usuario.id,
                veiculo_id=veiculo.id,
                status=StatusViagem.concluida,
                km_inicial=100,
                partida_em=datetime(2026, 5, 15, 2, 0, tzinfo=timezone.utc),
            )
        )
        db.flush()

        disponiveis = listar_veiculos_disponiveis_para_partida(db, usuario.id, hoje_local)
        ids_disponiveis = [veiculo_disponivel.id for veiculo_disponivel in disponiveis]

        assert veiculo.id in ids_disponiveis
    finally:
        db.rollback()
        db.close()


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-018"),
)
def test_veiculo_com_viagem_concluida_libera_para_outro_motorista_e_bloqueia_o_mesmo():
    """Apos a viagem ser finalizada (RN-018), o veiculo so continua bloqueado
    para nova partida do MESMO motorista no mesmo dia local (continuidade do
    hodometro); outro motorista deve poder usa-lo no mesmo dia."""
    db = SessionLocal()
    data_referencia = date(2026, 5, 20)

    try:
        motorista_original = Usuario(
            nome="Motorista Original",
            email="motorista.original.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        outro_motorista = Usuario(
            nome="Outro Motorista",
            email="outro.motorista.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([motorista_original, outro_motorista])
        db.flush()

        veiculo_empresa = Veiculo(
            placa="GGG6G66",
            modelo="Modelo Empresa Concluida",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        )
        db.add(veiculo_empresa)
        db.flush()

        db.add(
            Viagem(
                usuario_id=motorista_original.id,
                veiculo_id=veiculo_empresa.id,
                status=StatusViagem.concluida,
                km_inicial=100,
                km_final=150,
                partida_em=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
                chegada_em=datetime(2026, 5, 20, 13, 0, tzinfo=timezone.utc),
            )
        )
        db.flush()

        disponiveis_outro = listar_veiculos_disponiveis_para_partida(db, outro_motorista.id, data_referencia)
        disponiveis_original = listar_veiculos_disponiveis_para_partida(db, motorista_original.id, data_referencia)

        assert veiculo_empresa.id in [veiculo.id for veiculo in disponiveis_outro]
        assert veiculo_empresa.id not in [veiculo.id for veiculo in disponiveis_original]
    finally:
        db.rollback()
        db.close()


@pytest.mark.risco(
    peso=20,
    criticidade="media",
    area="modelo_dados",
    referencias=("RF-004",),
)
def test_normalizacao_modelo_veiculo_remove_marca_e_aplica_caixa_alta():
    assert normalizar_modelo_veiculo("honda/hrv") == "HRV"
    assert normalizar_modelo_veiculo(" VOLKSWAGEN POLO ") == "POLO"
    assert normalizar_modelo_veiculo("T-cross") == "T-CROSS"
    assert normalizar_modelo_veiculo("Onix") == "ONIX"
    assert normalizar_marca_veiculo(" chevrolet ") == "CHEVROLET"


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
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-020", "RN-027"),
)
def test_endpoint_lista_veiculos_em_rota_com_motorista(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get("/vehicles/in-route", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    veiculos = response_items(response)
    item = next((candidate for candidate in veiculos if candidate["viagem_id"] == trip["id"]), None)
    assert item is not None
    assert item["veiculo_id"] == trip["veiculo_id"]
    assert item["placa"] == trip["veiculo_placa"]
    assert item["modelo"] == trip["veiculo_modelo"]
    assert item["motorista_id"] == trip["usuario_id"]
    assert item["motorista_nome"] == trip["usuario_nome"]
    assert item["em_rota"] is True
    assert item["partida_em"]


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


@pytest.mark.autenticacao
@pytest.mark.risco(
    peso=100,
    criticidade="critica",
    area="autenticacao",
    referencias=("RN-001", "RN-027", "RNF-002"),
)
def test_endpoint_veiculos_em_rota_sem_token_retorna_401(api_client):
    response = api_client.get("/vehicles/in-route")

    assert_unauthorized(response)
