import pytest


@pytest.mark.risco(
    peso=5,
    criticidade="baixa",
    area="infra",
    referencias=("API-002", "ARQ-003"),
)
def test_health_check_retorna_status_da_api(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "Controle Itinerario Comercial Bello"

