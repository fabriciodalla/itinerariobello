import pytest

from assertions import assert_business_rule_violation, assert_unauthorized, assert_validation_error, json_body
from factories import start_payload, without_key, without_nested_key
from helpers import create_trip_in_progress, post_trip_start


@pytest.mark.viagem
@pytest.mark.foto
@pytest.mark.gps
@pytest.mark.km
@pytest.mark.risco(
    peso=100,
    criticidade="critica",
    area="viagem",
    referencias=("RF-004", "RF-005", "RF-006", "RF-007", "RN-001"),
)
def test_partida_valida_cria_viagem_em_andamento(api_client, motorista_auth_headers, test_vehicle_id):
    payload = start_payload(test_vehicle_id)

    response = post_trip_start(api_client, motorista_auth_headers, payload)

    assert response.status_code == 201, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data.get("id") or data.get("viagem_id")
    assert data["status"] == "em_andamento"
    assert str(data["veiculo_id"]) == str(test_vehicle_id)
    assert data["veiculo_placa"]
    assert data["veiculo_modelo"]
    assert float(data["km_inicial"]) == payload["km_inicial"]
    assert data.get("partida_em")
    assert data["foto_hodometro_inicial"]["download_url"].startswith("/photos/")


@pytest.mark.autenticacao
@pytest.mark.risco(peso=100, criticidade="critica", area="autenticacao", referencias=("RN-001", "RNF-002"))
def test_partida_sem_token_retorna_401(api_client, test_vehicle_id):
    response = post_trip_start(api_client, None, start_payload(test_vehicle_id))

    assert_unauthorized(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-004", "RN-002"))
def test_partida_sem_veiculo_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    payload = without_key(start_payload(test_vehicle_id), "veiculo_id")

    response = post_trip_start(api_client, motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-005", "RN-003"))
def test_partida_sem_km_inicial_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    payload = without_key(start_payload(test_vehicle_id), "km_inicial")

    response = post_trip_start(api_client, motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.gps
@pytest.mark.risco(peso=100, criticidade="critica", area="gps", referencias=("RF-007", "RN-005"))
def test_partida_sem_gps_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    payload = without_key(start_payload(test_vehicle_id), "gps")

    response = post_trip_start(api_client, motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.gps
@pytest.mark.parametrize("coordenada_obrigatoria", ("latitude", "longitude"))
@pytest.mark.risco(peso=100, criticidade="critica", area="gps", referencias=("RF-007", "RN-005"))
def test_partida_sem_latitude_ou_longitude_retorna_erro(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
    coordenada_obrigatoria,
):
    payload = without_nested_key(start_payload(test_vehicle_id), "gps", coordenada_obrigatoria)

    response = post_trip_start(api_client, motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.foto
@pytest.mark.risco(peso=100, criticidade="critica", area="foto", referencias=("RF-006", "RN-004"))
def test_partida_sem_foto_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    response = post_trip_start(
        api_client,
        motorista_auth_headers,
        start_payload(test_vehicle_id),
        include_photo=False,
    )

    assert_validation_error(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="viagem", referencias=("RF-004", "RN-018"))
def test_partida_bloqueada_quando_veiculo_ja_em_uso_no_dia(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_start(api_client, motorista_auth_headers, start_payload(test_vehicle_id))

    assert_business_rule_violation(response)
