from __future__ import annotations

import base64
import json
from copy import deepcopy
from typing import Any


SAMPLE_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA"
    "AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3"
    "ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp"
    "6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAA"
    "wEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx"
    "BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK"
    "U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3"
    "uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iii"
    "gD//2Q=="
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
