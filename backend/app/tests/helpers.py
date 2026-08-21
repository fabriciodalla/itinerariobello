from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

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


def backdate_trip_partida(trip_id: str, dias: int) -> None:
    """Move a partida_em da viagem 'dias' dias para tras, no fuso local do
    negocio, simulando um itinerario iniciado em um dia anterior. Usado para
    testar o fechamento tardio (RN-034 e RN-035 em docs/regras-negocio.md),
    ja que a API nao permite escolher a data de partida diretamente."""
    from app.db.session import SessionLocal
    from app.models.viagem import Viagem
    from app.services.veiculos import data_referencia_atual, intervalo_do_dia

    referencia = data_referencia_atual() - timedelta(days=dias)
    inicio_utc, _ = intervalo_do_dia(referencia)
    nova_partida = inicio_utc + timedelta(hours=8)

    db = SessionLocal()
    try:
        viagem = db.get(Viagem, UUID(str(trip_id)))
        if viagem is None:
            pytest.fail(f"Viagem {trip_id} nao encontrada para simular atraso no teste.", pytrace=False)
        viagem.partida_em = nova_partida
        db.commit()
    finally:
        db.close()
