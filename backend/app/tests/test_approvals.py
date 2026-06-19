from __future__ import annotations

import pytest

from assertions import assert_business_rule_violation, assert_monthly_closure_audit, json_body, response_items
from helpers import create_trip_ready_for_monthly_closure


def monthly_params() -> dict[str, int]:
    from datetime import date

    today = date.today()
    return {"ano": today.year, "mes": today.month}


@pytest.mark.aprovacao
@pytest.mark.risco(peso=100, criticidade="critica", area="aprovacao", referencias=("RF-018", "RN-022"))
def test_aprovacao_individual_por_viagem_foi_desativada(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.post(
        f"/trips/{trip['id']}/approve",
        json={},
        headers=aprovador_auth_headers,
    )

    assert response.status_code == 410, response.text


@pytest.mark.aprovacao
@pytest.mark.risco(peso=100, criticidade="critica", area="aprovacao", referencias=("RF-014", "RN-015", "RN-021"))
def test_superior_fecha_fechamento_mensal_do_motorista_e_registra_auditoria(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.post(
        f"/reports/monthly/closures/{trip['usuario_id']}/close",
        params=monthly_params(),
        json={"observacao": "Fechamento conferido no consolidado mensal."},
        headers=aprovador_auth_headers,
    )

    assert response.status_code == 200, response.text
    fechamento = json_body(response)
    assert isinstance(fechamento, dict)
    assert_monthly_closure_audit(
        fechamento,
        status="fechado",
        observacao="Fechamento conferido no consolidado mensal.",
    )
    assert fechamento["total_viagens"] >= 1

    trip_response = api_client.get(f"/trips/{trip['id']}", headers=motorista_auth_headers)
    assert trip_response.status_code == 200, trip_response.text
    assert json_body(trip_response)["status"] == "concluida"


@pytest.mark.aprovacao
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-014", "RF-016", "RN-021"))
def test_superior_consulta_fechamento_mensal_do_motorista(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    list_response = api_client.get(
        "/reports/monthly/closures",
        params=monthly_params(),
        headers=aprovador_auth_headers,
    )
    assert list_response.status_code == 200, list_response.text
    closures = response_items(list_response)
    assert any(str(item.get("motorista_id")) == trip["usuario_id"] for item in closures)

    detail_response = api_client.get(
        f"/reports/monthly/closures/{trip['usuario_id']}",
        params=monthly_params(),
        headers=aprovador_auth_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = json_body(detail_response)
    assert isinstance(detail, dict)
    assert detail["motorista_id"] == trip["usuario_id"]
    assert detail["status"] == "aberto"


@pytest.mark.aprovacao
@pytest.mark.parametrize("endpoint", ("approve", "reject"))
@pytest.mark.risco(peso=100, criticidade="critica", area="aprovacao", referencias=("RF-014", "RN-022"))
def test_endpoints_legados_de_aprovacao_do_fechamento_mensal_retornam_410(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
    endpoint,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.post(
        f"/reports/monthly/closures/{trip['usuario_id']}/{endpoint}",
        params=monthly_params(),
        json={},
        headers=aprovador_auth_headers,
    )

    assert response.status_code == 410, response.text


@pytest.mark.viagem
@pytest.mark.aprovacao
@pytest.mark.risco(peso=100, criticidade="critica", area="viagem", referencias=("RN-013", "RF-014"))
def test_superior_nao_edita_viagem_apos_fechamento_mensal_fechado(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)
    close_response = api_client.post(
        f"/reports/monthly/closures/{trip['usuario_id']}/close",
        params=monthly_params(),
        json={},
        headers=aprovador_auth_headers,
    )
    assert close_response.status_code == 200, close_response.text

    response = api_client.patch(
        f"/trips/{trip['id']}",
        json={"rota_utilizada": "Rota alterada apos fechamento fechado"},
        headers=aprovador_auth_headers,
    )

    assert_business_rule_violation(response)
