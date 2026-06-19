import pytest

from assertions import assert_business_rule_error, assert_unauthorized, assert_validation_error, json_body
from factories import finish_payload, without_key, without_nested_key
from helpers import create_trip_in_progress, post_trip_finish


@pytest.mark.viagem
@pytest.mark.foto
@pytest.mark.gps
@pytest.mark.km
@pytest.mark.risco(
    peso=100,
    criticidade="critica",
    area="viagem",
    referencias=("RF-008", "RF-009", "RF-010", "RF-011", "RF-012", "RN-010"),
)
def test_chegada_valida_envia_viagem_para_fechamento_mensal(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = finish_payload()

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert response.status_code in {200, 201}, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["status"] == "concluida"
    assert float(data["km_final"]) == payload["km_final"]
    assert float(data["km_rodado"]) == pytest.approx(payload["km_final"] - float(trip["km_inicial"]))
    assert data["rota_utilizada"] == payload["rota_utilizada"]
    assert data.get("chegada_em")
    assert data["veiculo_placa"]
    assert data["veiculo_modelo"]
    assert data["foto_hodometro_inicial"]["download_url"].startswith("/photos/")
    assert data["foto_hodometro_final"]["download_url"].startswith("/photos/")


@pytest.mark.autenticacao
@pytest.mark.risco(peso=100, criticidade="critica", area="autenticacao", referencias=("RN-001", "RNF-002"))
def test_chegada_sem_token_retorna_401(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_finish(api_client, trip["id"], None, finish_payload())

    assert_unauthorized(response)


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-008", "RN-007"))
def test_chegada_sem_km_final_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = without_key(finish_payload(), "km_final")

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.gps
@pytest.mark.risco(peso=100, criticidade="critica", area="gps", referencias=("RF-010", "RN-009"))
def test_chegada_sem_gps_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = without_key(finish_payload(), "gps")

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.gps
@pytest.mark.parametrize("coordenada_obrigatoria", ("latitude", "longitude"))
@pytest.mark.risco(peso=100, criticidade="critica", area="gps", referencias=("RF-010", "RN-009"))
def test_chegada_sem_latitude_ou_longitude_retorna_erro(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
    coordenada_obrigatoria,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = without_nested_key(finish_payload(), "gps", coordenada_obrigatoria)

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-011", "RN-012"))
def test_chegada_sem_rota_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = without_key(finish_payload(), "rota_utilizada")

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-011", "RN-012"))
def test_chegada_com_rota_em_branco_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = finish_payload(rota_utilizada="   ")

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_validation_error(response)


@pytest.mark.foto
@pytest.mark.risco(peso=100, criticidade="critica", area="foto", referencias=("RF-009", "RN-008"))
def test_chegada_sem_foto_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(),
        include_photo=False,
    )

    assert_validation_error(response)


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-012", "RN-011"))
def test_chegada_com_km_final_menor_que_inicial_retorna_erro(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = finish_payload(km_final=float(trip["km_inicial"]) - 1)

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert_business_rule_error(response)


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-012", "RN-011"))
def test_chegada_permite_km_final_igual_ao_inicial(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    payload = finish_payload(km_final=float(trip["km_inicial"]))

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, payload)

    assert response.status_code in {200, 201}, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["status"] == "concluida"
    assert float(data["km_rodado"]) == pytest.approx(0)
