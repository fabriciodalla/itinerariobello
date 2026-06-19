import pytest

from assertions import assert_unauthorized, response_items
from factories import finish_payload, start_payload, without_nested_key
from helpers import create_trip_ready_for_monthly_closure, post_trip_finish, post_trip_start


@pytest.mark.gps
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RNF-004"))
def test_listagem_de_gps_sem_token_retorna_401(api_client):
    response = api_client.get("/trips/00000000-0000-0000-0000-000000000000/gps")

    assert_unauthorized(response)


@pytest.mark.gps
@pytest.mark.risco(peso=50, criticidade="alta", area="gps", referencias=("RF-007", "RF-010", "RF-016", "RNF-004"))
def test_listagem_de_gps_da_viagem_retorna_partida_e_chegada(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get(f"/trips/{trip['id']}/gps", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    locations = response_items(response)
    tipos = {location.get("tipo") for location in locations}
    assert {"partida", "chegada"}.issubset(tipos)

    for location in locations:
        assert location.get("latitude") is not None, locations
        assert location.get("longitude") is not None, locations
        assert location.get("endereco_resolvido") in {True, False}, locations
        assert location.get("capturado_em"), locations


@pytest.mark.gps
@pytest.mark.risco(peso=50, criticidade="alta", area="gps", referencias=("RF-007", "RF-010", "RN-023"))
def test_listagem_de_gps_informa_endereco_nao_resolvido_quando_indisponivel(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
    monkeypatch,
):
    import app.api.routes.trips as trips_route

    monkeypatch.setattr(trips_route, "reverse_geocode", lambda latitude, longitude, settings: None)
    start_data = without_nested_key(start_payload(test_vehicle_id), "gps", "endereco")
    start_response = post_trip_start(api_client, motorista_auth_headers, start_data)
    assert start_response.status_code == 201, start_response.text
    trip_id = start_response.json()["id"]

    finish_data = without_nested_key(finish_payload(), "gps", "endereco")
    finish_response = post_trip_finish(api_client, trip_id, motorista_auth_headers, finish_data)
    assert finish_response.status_code == 200, finish_response.text

    response = api_client.get(f"/trips/{trip_id}/gps", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    locations = response_items(response)
    assert len(locations) == 2
    for location in locations:
        assert location["endereco"] is None, locations
        assert location["endereco_resolvido"] is False, locations
        assert location["endereco_exibicao"] == "Endereco nao resolvido", locations
