from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.enums import TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.veiculos import VeiculoCreateRequest, VeiculoResponse
from app.services.veiculos import listar_veiculos_disponiveis_para_partida

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def to_response(veiculo: Veiculo, usuario_id) -> VeiculoResponse:
    return VeiculoResponse(
        id=veiculo.id,
        placa=veiculo.placa,
        modelo=veiculo.modelo,
        unidade=veiculo.unidade,
        categoria=veiculo.categoria,
        tipo=veiculo.tipo,
        tipo_disponibilidade=veiculo.tipo_disponibilidade,
        usuario_responsavel_id=veiculo.usuario_responsavel_id,
        ativo=veiculo.ativo,
        prioritario=veiculo.usuario_responsavel_id == usuario_id,
    )


@router.get("", response_model=list[VeiculoResponse])
def list_vehicles(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VeiculoResponse]:
    hoje = datetime.now(timezone.utc).date()
    veiculos = listar_veiculos_disponiveis_para_partida(db, usuario.id, hoje)
    return [to_response(veiculo, usuario.id) for veiculo in veiculos]


@router.post("", response_model=VeiculoResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VeiculoCreateRequest,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> VeiculoResponse:
    placa = payload.placa.strip().upper()
    existente = db.scalar(select(Veiculo).where(Veiculo.placa == placa))
    if existente is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Veiculo ja cadastrado.")

    disponibilidade = payload.tipo_disponibilidade
    if disponibilidade is None:
        disponibilidade = (
            TipoDisponibilidadeVeiculo.fixo
            if payload.tipo == TipoVeiculo.proprio
            else TipoDisponibilidadeVeiculo.alocado
        )

    if disponibilidade == TipoDisponibilidadeVeiculo.fixo and payload.usuario_responsavel_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Veiculo fixo exige usuario responsavel.",
        )

    veiculo = Veiculo(
        placa=placa,
        modelo=payload.modelo.strip(),
        unidade=payload.unidade.strip() if payload.unidade else None,
        categoria=payload.categoria.strip() if payload.categoria else None,
        tipo=payload.tipo,
        tipo_disponibilidade=disponibilidade,
        usuario_responsavel_id=payload.usuario_responsavel_id,
        ativo=payload.ativo,
    )
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return to_response(veiculo, payload.usuario_responsavel_id)
