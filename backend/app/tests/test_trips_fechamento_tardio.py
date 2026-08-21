from __future__ import annotations

from datetime import datetime

import pytest

from assertions import assert_business_rule_violation, assert_validation_error, json_body, response_items
from factories import finish_payload, start_payload
from helpers import backdate_trip_partida, create_trip_in_progress, post_trip_finish, post_trip_start


def current_report_params(trip: dict) -> dict[str, int]:
    partida = datetime.fromisoformat(trip["partida_em"].replace("Z", "+00:00"))
    return {"ano": partida.year, "mes": partida.month}


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-022", "RN-035"))
def test_chegada_no_mesmo_dia_nao_marca_fechamento_tardio(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, finish_payload())

    assert response.status_code in {200, 201}, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["fechamento_tardio"] is False
    assert data["pendente_fechamento_tardio"] is False
    assert data["motivo_fechamento_tardio"] is None


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-022", "RN-035"))
def test_chegada_em_outro_dia_sem_motivo_retorna_erro(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)

    response = post_trip_finish(api_client, trip["id"], motorista_auth_headers, finish_payload())

    assert_validation_error(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-022", "RN-035"))
def test_chegada_em_outro_dia_com_motivo_marca_fechamento_tardio(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)
    motivo = "Cliente atrasou a entrega e o motorista so retornou apos o expediente."

    response = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(motivo_fechamento_tardio=motivo),
    )

    assert response.status_code in {200, 201}, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["status"] == "concluida"
    assert data["fechamento_tardio"] is True
    assert data["pendente_fechamento_tardio"] is False
    assert data["motivo_fechamento_tardio"] == motivo


@pytest.mark.viagem
@pytest.mark.risco(peso=50, criticidade="alta", area="viagem", referencias=("RF-022", "RN-034"))
def test_viagem_atrasada_ainda_em_andamento_fica_sinalizada_como_pendente(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)

    response = api_client.get(f"/trips/{trip['id']}", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data["status"] == "em_andamento"
    assert data["pendente_fechamento_tardio"] is True
    assert data["fechamento_tardio"] is False


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-022", "RN-034"))
def test_partida_bloqueada_quando_existe_viagem_atrasada_pendente(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)

    response = post_trip_start(api_client, motorista_auth_headers, start_payload(test_vehicle_id))

    assert_business_rule_violation(response)


@pytest.mark.viagem
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RF-022", "RN-034"))
def test_partida_permitida_apos_resolver_viagem_atrasada(
    api_client,
    motorista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)
    finish_response = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(motivo_fechamento_tardio="Fechamento retroativo para liberar nova viagem."),
    )
    assert finish_response.status_code in {200, 201}, finish_response.text

    response = post_trip_start(api_client, motorista_auth_headers, start_payload(test_vehicle_id))

    assert response.status_code == 201, response.text


@pytest.mark.relatorio
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RN-035"))
def test_superior_visualiza_fechamento_tardio_no_relatorio_mensal(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    backdate_trip_partida(trip["id"], dias=1)
    motivo = "Viagem finalizada no dia seguinte por pane no veiculo."
    finish_response = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(motivo_fechamento_tardio=motivo),
    )
    assert finish_response.status_code in {200, 201}, finish_response.text
    finished = json_body(finish_response)
    assert isinstance(finished, dict)

    response = api_client.get(
        "/reports/monthly",
        params=current_report_params(finished),
        headers=aprovador_auth_headers,
    )

    assert response.status_code == 200, response.text
    items = response_items(response)
    trip_item = next((item for item in items if str(item.get("id")) == trip["id"]), None)
    assert trip_item is not None, f"Relatorio mensal deve conter a viagem {trip['id']}: {items}"
    assert trip_item["fechamento_tardio"] is True
    assert trip_item["motivo_fechamento_tardio"] == motivo
