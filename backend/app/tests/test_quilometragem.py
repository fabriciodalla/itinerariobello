"""Consistencia de quilometragem na partida/chegada (RF-025, RN-041 a RN-043)."""

from __future__ import annotations

import pytest

from assertions import assert_validation_error, json_body, response_items
from factories import finish_payload, start_payload
from helpers import (
    backdate_trip_partida,
    create_trip_in_progress,
    create_trip_ready_for_monthly_closure,
    post_trip_finish,
    post_trip_start,
)

# Valor padrao de KM_LIMITE_ATIPICO.
LIMITE = 1000


def _km_chegada(trip: dict) -> float:
    return float(trip["km_final"])


def _viagem_concluida_ontem(api_client, headers, veiculo_id) -> dict:
    """Viagem concluida com partida no dia anterior: o mesmo motorista so pode
    reutilizar o carro em outro dia (RN-018), entao a nova partida e 'hoje'."""
    trip = create_trip_ready_for_monthly_closure(api_client, headers, veiculo_id)
    backdate_trip_partida(trip["id"], dias=1)
    return trip


@pytest.mark.km
@pytest.mark.risco(peso=100, criticidade="critica", area="km", referencias=("RF-025", "RN-041"))
def test_partida_com_km_abaixo_do_ultimo_registro_do_veiculo_e_bloqueada(
    api_client, motorista_auth_headers, test_vehicle_id
):
    anterior = _viagem_concluida_ontem(api_client, motorista_auth_headers, test_vehicle_id)
    km_chegada = _km_chegada(anterior)

    response = post_trip_start(
        api_client, motorista_auth_headers, start_payload(test_vehicle_id, km_inicial=km_chegada - 10)
    )

    assert_validation_error(response)
    detail = json_body(response)["detail"]
    assert "maior ou igual a 12.410,8 km" in detail
    assert "ultimo km de chegada" in detail


@pytest.mark.km
@pytest.mark.risco(peso=50, criticidade="alta", area="km", referencias=("RF-025", "RN-041"))
def test_partida_com_km_igual_ao_ultimo_registro_e_permitida(api_client, motorista_auth_headers, test_vehicle_id):
    anterior = _viagem_concluida_ontem(api_client, motorista_auth_headers, test_vehicle_id)

    response = post_trip_start(
        api_client, motorista_auth_headers, start_payload(test_vehicle_id, km_inicial=_km_chegada(anterior))
    )

    assert response.status_code == 201, response.text


@pytest.mark.km
@pytest.mark.risco(peso=50, criticidade="alta", area="km", referencias=("RF-025", "RN-042"))
def test_partida_com_salto_atipico_exige_confirmacao(api_client, motorista_auth_headers, test_vehicle_id):
    anterior = _viagem_concluida_ontem(api_client, motorista_auth_headers, test_vehicle_id)
    km_absurdo = _km_chegada(anterior) * 10

    sem_confirmacao = post_trip_start(
        api_client, motorista_auth_headers, start_payload(test_vehicle_id, km_inicial=km_absurdo)
    )
    assert_validation_error(sem_confirmacao)
    assert "Revise o valor" in json_body(sem_confirmacao)["detail"]

    com_confirmacao = post_trip_start(
        api_client,
        motorista_auth_headers,
        start_payload(test_vehicle_id, km_inicial=km_absurdo, confirmar_km_atipico=True),
    )
    assert com_confirmacao.status_code == 201, com_confirmacao.text


@pytest.mark.km
@pytest.mark.risco(peso=50, criticidade="alta", area="km", referencias=("RF-025", "RN-043"))
def test_chegada_com_km_rodado_atipico_exige_confirmacao(api_client, motorista_auth_headers, test_vehicle_id):
    trip = create_trip_in_progress(api_client, motorista_auth_headers, test_vehicle_id)
    km_final_absurdo = float(trip["km_inicial"]) + LIMITE + 1

    sem_confirmacao = post_trip_finish(
        api_client, trip["id"], motorista_auth_headers, finish_payload(km_final=km_final_absurdo)
    )
    assert_validation_error(sem_confirmacao)
    assert "Revise o valor" in json_body(sem_confirmacao)["detail"]

    com_confirmacao = post_trip_finish(
        api_client,
        trip["id"],
        motorista_auth_headers,
        finish_payload(km_final=km_final_absurdo, confirmar_km_atipico=True),
    )
    assert com_confirmacao.status_code == 200, com_confirmacao.text
    assert float(json_body(com_confirmacao)["km_rodado"]) == pytest.approx(LIMITE + 1)


@pytest.mark.km
@pytest.mark.risco(peso=20, criticidade="media", area="km", referencias=("RF-025", "RN-041", "RN-042"))
def test_lista_de_veiculos_para_partida_informa_ultimo_km(api_client, motorista_auth_headers, test_vehicle_id):
    anterior = _viagem_concluida_ontem(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get("/vehicles", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    veiculo = next(item for item in response_items(response) if item["id"] == str(test_vehicle_id))
    assert float(veiculo["ultimo_km"]) == pytest.approx(_km_chegada(anterior))
    assert float(veiculo["km_limite_atipico"]) == LIMITE
