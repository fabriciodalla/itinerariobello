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
from app.models.viagem import Viagem
from app.schemas.veiculos import VeiculoCreateRequest, VeiculoEmRotaResponse, VeiculoPatchRequest, VeiculoResponse
from app.services.veiculos import listar_veiculos_disponiveis_para_partida, listar_veiculos_em_rota

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _primeiro_nome(nome: str | None) -> str | None:
    if not nome:
        return None
    return nome.strip().split()[0]


def to_response(veiculo: Veiculo, usuario_id) -> VeiculoResponse:
    responsavel = veiculo.usuario_responsavel
    return VeiculoResponse(
        id=veiculo.id,
        placa=veiculo.placa,
        modelo=veiculo.modelo,
        marca=veiculo.marca,
        unidade=veiculo.unidade,
        categoria=veiculo.categoria,
        tipo=veiculo.tipo,
        tipo_disponibilidade=veiculo.tipo_disponibilidade,
        usuario_responsavel_id=veiculo.usuario_responsavel_id,
        responsavel_nome=_primeiro_nome(responsavel.nome) if responsavel else None,
        ativo=veiculo.ativo,
        prioritario=veiculo.usuario_responsavel_id == usuario_id,
    )


def to_em_rota_response(viagem: Viagem) -> VeiculoEmRotaResponse:
    return VeiculoEmRotaResponse(
        viagem_id=viagem.id,
        veiculo_id=viagem.veiculo_id,
        placa=viagem.veiculo.placa,
        modelo=viagem.veiculo.modelo,
        motorista_id=viagem.usuario_id,
        motorista_nome=viagem.usuario.nome,
        em_rota=True,
        partida_em=viagem.partida_em,
    )


@router.get("", response_model=list[VeiculoResponse])
def list_vehicles(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VeiculoResponse]:
    hoje = datetime.now(timezone.utc).date()
    veiculos = listar_veiculos_disponiveis_para_partida(db, usuario.id, hoje)
    return [to_response(veiculo, usuario.id) for veiculo in veiculos]


@router.get("/in-route", response_model=list[VeiculoEmRotaResponse])
def list_vehicles_in_route(
    _: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VeiculoEmRotaResponse]:
    return [to_em_rota_response(viagem) for viagem in listar_veiculos_em_rota(db)]


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
        marca=payload.marca.strip() if payload.marca else None,
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


@router.get("/all", response_model=list[VeiculoResponse])
def list_all_vehicles(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VeiculoResponse]:
    veiculos = list(db.scalars(select(Veiculo).order_by(Veiculo.placa)).all())
    return [to_response(v, None) for v in veiculos]


@router.patch("/{veiculo_id}", response_model=VeiculoResponse)
def patch_vehicle(
    veiculo_id: str,
    payload: VeiculoPatchRequest,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> VeiculoResponse:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veiculo nao encontrado.")

    fields = payload.model_fields_set

    if "usuario_responsavel_id" in fields:
        if payload.usuario_responsavel_id is not None and db.get(Usuario, payload.usuario_responsavel_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Usuario responsavel nao encontrado.",
            )
        veiculo.usuario_responsavel_id = payload.usuario_responsavel_id

    if "tipo_disponibilidade" in fields and payload.tipo_disponibilidade is not None:
        veiculo.tipo_disponibilidade = payload.tipo_disponibilidade

    if "unidade" in fields:
        veiculo.unidade = payload.unidade.strip() if payload.unidade else None

    if "ativo" in fields and payload.ativo is not None:
        veiculo.ativo = payload.ativo

    if veiculo.tipo_disponibilidade == TipoDisponibilidadeVeiculo.fixo and veiculo.usuario_responsavel_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Veiculo fixo exige usuario responsavel.",
        )

    db.commit()
    db.refresh(veiculo)
    return to_response(veiculo, None)
