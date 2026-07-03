from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assertions import assert_unauthorized


@pytest.fixture
def geocoding_auth_headers(api_client):
    from app.api.deps import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), ativo=True)
    yield {"Authorization": "Bearer token-de-teste"}
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.gps
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-007", "RF-010", "RNF-004"))
def test_geocodificacao_reversa_sem_token_retorna_401(api_client):
    response = api_client.get("/geocoding/reverse?latitude=-23.55052&longitude=-46.633308")

    assert_unauthorized(response)


@pytest.mark.gps
@pytest.mark.risco(peso=50, criticidade="alta", area="gps", referencias=("RF-007", "RF-010", "RN-023"))
def test_geocodificacao_reversa_retorna_endereco_resolvido(api_client, geocoding_auth_headers, monkeypatch):
    import app.api.routes.geocoding as geocoding_route

    def fake_reverse_geocode(latitude: Decimal, longitude: Decimal, settings: object) -> str:
        assert latitude == Decimal("-23.55052")
        assert longitude == Decimal("-46.633308")
        return " Rua Teste, Cidade - UF "

    monkeypatch.setattr(geocoding_route, "reverse_geocode", fake_reverse_geocode)

    response = api_client.get(
        "/geocoding/reverse?latitude=-23.55052&longitude=-46.633308",
        headers=geocoding_auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "endereco": "Rua Teste, Cidade - UF",
        "endereco_resolvido": True,
        "endereco_exibicao": "Rua Teste, Cidade - UF",
    }


@pytest.mark.gps
@pytest.mark.risco(peso=20, criticidade="media", area="gps", referencias=("RF-007", "RF-010", "RN-023"))
def test_geocodificacao_reversa_desabilitada_retorna_endereco_nulo(api_client, geocoding_auth_headers, monkeypatch):
    import app.api.routes.geocoding as geocoding_route

    monkeypatch.setattr(
        geocoding_route,
        "get_settings",
        lambda: SimpleNamespace(reverse_geocoding_enabled=False),
    )

    response = api_client.get(
        "/geocoding/reverse?latitude=-23.55052&longitude=-46.633308",
        headers=geocoding_auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "endereco": None,
        "endereco_resolvido": False,
        "endereco_exibicao": "Endereco nao resolvido",
    }


@pytest.mark.gps
@pytest.mark.risco(peso=20, criticidade="media", area="gps", referencias=("RF-007", "RF-010", "RN-023"))
def test_geocodificacao_reversa_formata_endereco_com_numero_quando_disponivel(monkeypatch):
    from app.services import geocoding as geocoding_service

    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "display_name": "Rua Teste, Centro, Cidade - UF, Brasil",
                "address": {
                    "road": "Rua Teste",
                    "house_number": "123",
                    "suburb": "Centro",
                    "city": "Cidade",
                    "state": "UF",
                    "country": "Brasil",
                },
            }

    class FakeClient:
        def __init__(self, timeout: float):
            captured["timeout"] = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def get(self, url: str, params: dict[str, object], headers: dict[str, str]) -> FakeResponse:
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(geocoding_service.httpx, "Client", FakeClient)

    endereco = geocoding_service.reverse_geocode(
        Decimal("-23.55052"),
        Decimal("-46.633308"),
        SimpleNamespace(
            reverse_geocoding_enabled=True,
            reverse_geocoding_provider="nominatim",
            reverse_geocoding_timeout_seconds=5,
            reverse_geocoding_user_agent="itinerario-bello-teste/0.1",
            nominatim_reverse_url="https://nominatim.openstreetmap.org/reverse",
        ),
    )

    assert endereco == "Rua Teste, 123, Centro, Cidade - UF, Brasil"
    assert captured["params"] == {
        "format": "jsonv2",
        "lat": "-23.55052",
        "lon": "-46.633308",
        "addressdetails": 1,
        "accept-language": "pt-BR",
    }


@pytest.mark.gps
@pytest.mark.risco(peso=20, criticidade="media", area="gps", referencias=("RF-007", "RF-010", "RN-023"))
def test_geocodificacao_reversa_nao_inventa_numero_quando_provedor_nao_informa():
    from app.services.geocoding import formatar_endereco_nominatim

    endereco = formatar_endereco_nominatim(
        {
            "display_name": "Rua Sem Numero, Centro, Cidade - UF, Brasil",
            "address": {
                "road": "Rua Sem Numero",
                "suburb": "Centro",
                "city": "Cidade",
                "state": "UF",
                "country": "Brasil",
            },
        }
    )

    assert endereco == "Rua Sem Numero, Centro, Cidade - UF, Brasil"
