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
                    "addressdetails": 0,
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
    return normalizar_endereco(data.get("display_name"))
