from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from app.core.config import Settings


def normalizar_endereco(endereco: object) -> str | None:
    if not isinstance(endereco, str):
        return None
    endereco_limpo = endereco.strip()
    return endereco_limpo or None


def _address_value(address: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = normalizar_endereco(address.get(key))
        if value:
            return value
    return None


def cidade_estado(cidade: str | None, estado: str | None) -> str | None:
    if cidade and estado:
        return f"{cidade} - {estado}"
    return cidade or estado


def formatar_endereco_nominatim(data: dict[str, Any]) -> str | None:
    display_name = normalizar_endereco(data.get("display_name"))
    address = data.get("address")
    if not isinstance(address, dict):
        return display_name

    logradouro = _address_value(address, "road", "pedestrian", "footway", "residential", "path", "cycleway")
    numero = _address_value(address, "house_number")
    bairro = _address_value(address, "suburb", "neighbourhood", "city_district", "quarter")
    cidade = _address_value(address, "city", "town", "village", "municipality", "county")
    estado = _address_value(address, "state")
    pais = _address_value(address, "country")
    ponto_referencia = _address_value(address, "building", "amenity", "shop", "tourism")

    partes: list[str] = []
    if logradouro and numero:
        partes.append(f"{logradouro}, {numero}")
    elif logradouro:
        partes.append(logradouro)
    elif ponto_referencia:
        partes.append(ponto_referencia)

    for parte in (bairro, cidade_estado(cidade, estado), pais):
        if parte and parte not in partes:
            partes.append(parte)

    return normalizar_endereco(", ".join(partes)) or display_name


def reverse_geocode(latitude: Decimal, longitude: Decimal, settings: Settings) -> str | None:
    if not settings.reverse_geocoding_enabled:
        return None
    if settings.reverse_geocoding_provider != "nominatim":
        return None

    try:
        with httpx.Client(timeout=settings.reverse_geocoding_timeout_seconds) as client:
            response = client.get(
                settings.nominatim_reverse_url,
                params={
                    "format": "jsonv2",
                    "lat": str(latitude),
                    "lon": str(longitude),
                    "addressdetails": 1,
                    "accept-language": "pt-BR",
                },
                headers={"User-Agent": settings.reverse_geocoding_user_agent},
            )
            response.raise_for_status()
            data: Any = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    if not isinstance(data, dict):
        return None
    return formatar_endereco_nominatim(data)
