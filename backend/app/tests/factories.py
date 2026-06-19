from __future__ import annotations

import json
from copy import deepcopy
from typing import Any


SAMPLE_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
    b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9"
)
INVALID_TEXT_FILE = b"arquivo invalido para teste"


def start_payload(veiculo_id: str, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "veiculo_id": veiculo_id,
        "km_inicial": 12345.6,
        "gps": {
            "latitude": -23.55052,
            "longitude": -46.633308,
            "precisao_metros": 12.5,
            "endereco": "Praca da Se, Sao Paulo - SP, Brasil",
        },
    }
    payload.update(overrides)
    return payload


def finish_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "km_final": 12410.8,
        "rota_utilizada": "Cliente A -> Cliente B -> Unidade Bello",
        "gps": {
            "latitude": -23.551,
            "longitude": -46.634,
            "precisao_metros": 10.0,
            "endereco": "Avenida Paulista, Sao Paulo - SP, Brasil",
        },
    }
    payload.update(overrides)
    return payload


def without_key(payload: dict[str, Any], key: str) -> dict[str, Any]:
    new_payload = deepcopy(payload)
    new_payload.pop(key, None)
    return new_payload


def without_nested_key(payload: dict[str, Any], parent_key: str, key: str) -> dict[str, Any]:
    new_payload = deepcopy(payload)
    new_payload[parent_key].pop(key, None)
    return new_payload


def multipart_payload(
    payload: dict[str, Any],
    *,
    include_photo: bool = True,
    filename: str = "hodometro.jpg",
    content_type: str = "image/jpeg",
    content: bytes = SAMPLE_JPEG,
) -> dict[str, Any]:
    request: dict[str, Any] = {"data": {"payload": json.dumps(payload)}}
    if include_photo:
        request["files"] = {
            "foto_hodometro": (filename, content, content_type),
        }
    return request
