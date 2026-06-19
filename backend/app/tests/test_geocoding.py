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
