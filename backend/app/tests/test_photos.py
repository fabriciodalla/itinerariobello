import pytest
from sqlalchemy import delete, select

from assertions import assert_validation_error, response_items
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.foto_hodometro import FotoHodometro
from app.models.localizacao_gps import LocalizacaoGPS
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from factories import INVALID_TEXT_FILE, finish_payload, start_payload
from helpers import (
    create_trip_in_progress,
    create_trip_ready_for_monthly_closure,
    post_trip_finish,
    post_trip_start,
)
from uuid import uuid4


@pytest.mark.foto
@pytest.mark.risco(peso=50, criticidade="alta", area="foto", referencias=("RF-006", "RNF-006"))
def test_partida_rejeita_arquivo_que_nao_e_imagem(api_client, motorista_auth_headers, test_vehicle_id):
    response = post_trip_start(
        api_client,
        motorista_auth_headers,
        start_payload(test_vehicle_id),
        filename="hodometro.txt",
        content_type="text/plain",
        content=INVALID_TEXT_FILE,
    )

    assert_validation_error(response)


@pytest.mark.foto
@pytest.mark.risco(peso=50, criticidade="alta", area="foto", referencias=("RF-009", "RNF-006"))
def test_chegada_rejeita_arquivo_que_nao_e_imagem(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(),
        filename="hodometro-final.txt",
        content_type="text/plain",
        content=INVALID_TEXT_FILE,
    )

    assert_validation_error(response)


@pytest.mark.foto
@pytest.mark.risco(peso=50, criticidade="alta", area="foto", referencias=("RF-006", "RF-009", "RNF-006"))
def test_listagem_de_fotos_da_viagem_retorna_partida_e_chegada(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get(f"/trips/{trip['id']}/photos", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    photos = response_items(response)
    tipos = {photo.get("tipo") for photo in photos}
    assert {"inicial", "final"}.issubset(tipos)
    for photo in photos:
        assert photo.get("download_url") == f"/photos/{photo['id']}"


@pytest.mark.foto
@pytest.mark.risco(peso=50, criticidade="alta", area="foto", referencias=("RF-006", "RF-009", "RNF-004", "RNF-006"))
def test_download_de_foto_da_viagem_retorna_conteudo(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)
    photos_response = api_client.get(f"/trips/{trip['id']}/photos", headers=motorista_auth_headers)
    assert photos_response.status_code == 200, photos_response.text
    photos = response_items(photos_response)
    photo_id = next(
        (
            photo.get("id") or photo.get("foto_id")
            for photo in photos
            if photo.get("id") or photo.get("foto_id")
        ),
        None,
    )
    assert photo_id, f"Listagem de fotos deve retornar id ou foto_id: {photos}"

    response = api_client.get(f"/photos/{photo_id}", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    assert response.content


@pytest.mark.foto
@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="foto", referencias=("RF-013", "RF-016", "RNF-004"))
def test_historico_de_viagens_retorna_veiculo_e_fotos_para_visualizacao(
    api_client,
):
    settings = get_settings()
    db = SessionLocal()
    usuario_id = None
    veiculo_id = None
    try:
        suffix = uuid4().hex[:8]
        usuario = Usuario(
            nome="Motorista Historico Fotos Teste",
            email=f"motorista.historico.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add(usuario)
        db.flush()
        usuario_id = usuario.id

        veiculo = Veiculo(
            placa=f"HIS{suffix[:4].upper()}",
            modelo="Veiculo Historico Fotos",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=usuario.id,
        )
        db.add(veiculo)
        db.commit()
        veiculo_id = veiculo.id

        token = create_access_token(str(usuario.id), settings.secret_key, settings.access_token_expire_minutes)
        headers = {"Authorization": f"Bearer {token}"}
        trip = create_trip_in_progress(api_client, headers, str(veiculo.id))
        finish_response = post_trip_finish(api_client, trip["id"], headers, finish_payload())
        assert finish_response.status_code in {200, 201}, finish_response.text

        response = api_client.get("/trips", headers=headers)

        assert response.status_code == 200, response.text
        trips = response_items(response)
        item = next((candidate for candidate in trips if candidate["id"] == trip["id"]), None)
        assert item is not None
        assert item["veiculo_placa"] == veiculo.placa
        assert item["veiculo_modelo"] == veiculo.modelo
        assert item["foto_hodometro_inicial"]["download_url"].startswith("/photos/")
        assert item["foto_hodometro_final"]["download_url"].startswith("/photos/")
    finally:
        db.rollback()
        if usuario_id is not None:
            trip_ids = select(Viagem.id).where(Viagem.usuario_id == usuario_id)
            db.execute(delete(LocalizacaoGPS).where(LocalizacaoGPS.viagem_id.in_(trip_ids)))
            db.execute(delete(FotoHodometro).where(FotoHodometro.viagem_id.in_(trip_ids)))
            db.execute(delete(Viagem).where(Viagem.usuario_id == usuario_id))
        if veiculo_id is not None:
            db.execute(delete(Veiculo).where(Veiculo.id == veiculo_id))
        if usuario_id is not None:
            db.execute(delete(Usuario).where(Usuario.id == usuario_id))
        db.commit()
        db.close()
