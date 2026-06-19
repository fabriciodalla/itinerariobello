from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.usuario import Usuario
from app.schemas.geocoding import ReverseGeocodeResponse
from app.services.geocoding import normalizar_endereco, reverse_geocode

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


@router.get("/reverse", response_model=ReverseGeocodeResponse)
def reverse_geocoding_lookup(
    latitude: Annotated[Decimal, Query(ge=-90, le=90)],
    longitude: Annotated[Decimal, Query(ge=-180, le=180)],
    _usuario: Annotated[Usuario, Depends(get_current_user)],
) -> ReverseGeocodeResponse:
    settings = get_settings()
    endereco = normalizar_endereco(reverse_geocode(latitude, longitude, settings))
    return ReverseGeocodeResponse(endereco=endereco)
