from __future__ import annotations

from typing import Any


def json_body(response) -> dict[str, Any] | list[Any]:
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(f"Resposta nao retornou JSON valido: {response.text}") from exc


def assert_validation_error(response) -> None:
    assert response.status_code in {400, 422}, response.text


def assert_business_rule_error(response) -> None:
    assert response.status_code in {400, 409, 422}, response.text


def assert_blocked_operation(response) -> None:
    assert response.status_code in {400, 403, 409, 422}, response.text


def assert_permission_denied(response) -> None:
    assert response.status_code == 403, response.text


def assert_business_rule_violation(response) -> None:
    assert response.status_code == 409, response.text


def assert_unauthorized(response) -> None:
    assert response.status_code == 401, response.text


def assert_forbidden(response) -> None:
    assert response.status_code == 403, response.text


def response_items(response) -> list[dict[str, Any]]:
    data = json_body(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "data", "resultados", "viagens", "fotos", "aprovacoes", "registros"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    raise AssertionError(f"Resposta nao possui lista de itens: {data}")


def assert_has_any_key(data: dict[str, Any], *keys: str) -> None:
    assert any(data.get(key) is not None for key in keys), (
        f"Resposta deve conter pelo menos um destes campos: {keys}. Corpo: {data}"
    )


def assert_monthly_closure_audit(
    fechamento: dict[str, Any],
    *,
    status: str,
    observacao: str | None = None,
) -> None:
    assert fechamento.get("status") == status, fechamento
    assert fechamento.get("superior_id"), fechamento
    assert fechamento.get("avaliado_em"), fechamento
    assert fechamento.get("motorista_id"), fechamento
    assert fechamento.get("ano"), fechamento
    assert fechamento.get("mes"), fechamento
    if observacao is not None:
        assert fechamento.get("observacao") == observacao, fechamento
