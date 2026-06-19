from __future__ import annotations

from typing import Any

import pytest

from assertions import json_body
from factories import finish_payload, multipart_payload, start_payload


def post_trip_start(api_client, headers: dict[str, str] | None, payload: dict[str, Any], **photo_options):
    request = multipart_payload(payload, **photo_options)
    return api_client.post("/trips/start", headers=headers, **request)


def post_trip_finish(
    api_client,
    trip_id: str,
    headers: dict[str, str] | None,
    payload: dict[str, Any],
    **photo_options,
):
    request = multipart_payload(payload, **photo_options)
    return api_client.post(f"/trips/{trip_id}/finish", headers=headers, **request)


def extract_trip_id(data: dict[str, Any]) -> str:
    trip_id = data.get("id") or data.get("viagem_id")
    if not trip_id:
        pytest.fail(f"Resposta da viagem deve conter id ou viagem_id: {data}", pytrace=False)
    return str(trip_id)


def create_trip_in_progress(api_client, headers: dict[str, str], veiculo_id: str) -> dict[str, Any]:
    response = post_trip_start(api_client, headers, start_payload(veiculo_id))
    if response.status_code != 201:
        pytest.fail(
            "Nao foi possivel criar viagem em andamento para o teste. "
            f"Status: {response.status_code}. Corpo: {response.text}",
            pytrace=False,
        )
    data = json_body(response)
    if not isinstance(data, dict):
        pytest.fail(f"Resposta de partida deve ser objeto JSON: {data}", pytrace=False)
    data["id"] = extract_trip_id(data)
    return data


def create_trip_ready_for_monthly_closure(api_client, headers: dict[str, str], veiculo_id: str) -> dict[str, Any]:
    trip = create_trip_in_progress(api_client, headers, veiculo_id)
    response = post_trip_finish(api_client, trip["id"], headers, finish_payload())
    if response.status_code not in {200, 201}:
        pytest.fail(
            "Nao foi possivel finalizar viagem para o teste. "
            f"Status: {response.status_code}. Corpo: {response.text}",
            pytrace=False,
        )
    data = json_body(response)
    if not isinstance(data, dict):
        pytest.fail(f"Resposta de chegada deve ser objeto JSON: {data}", pytrace=False)
    data["id"] = extract_trip_id(data) if data.get("id") or data.get("viagem_id") else trip["id"]
    return data
