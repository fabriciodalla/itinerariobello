from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TipoDisponibilidadeVeiculo, TipoVeiculo


class VeiculoResponse(BaseModel):
    id: UUID
    placa: str
    modelo: str
    marca: str | None = None
    unidade: str | None = None
    categoria: str | None = None
    tipo: TipoVeiculo
    tipo_disponibilidade: TipoDisponibilidadeVeiculo
    usuario_responsavel_id: UUID | None = None
    responsavel_nome: str | None = None
    ativo: bool
    prioritario: bool = False


class VeiculoEmRotaResponse(BaseModel):
    viagem_id: UUID
    veiculo_id: UUID
    placa: str
    modelo: str
    motorista_id: UUID
    motorista_nome: str
    em_rota: bool
    partida_em: datetime


class VeiculoCreateRequest(BaseModel):
    placa: str = Field(min_length=1, max_length=10)
    modelo: str = Field(min_length=1, max_length=120)
    marca: str | None = Field(default=None, max_length=80)
    tipo: TipoVeiculo
    tipo_disponibilidade: TipoDisponibilidadeVeiculo | None = None
    usuario_responsavel_id: UUID | None = None
    unidade: str | None = Field(default=None, max_length=120)
    categoria: str | None = Field(default=None, max_length=120)
    ativo: bool = True


class VeiculoPatchRequest(BaseModel):
    usuario_responsavel_id: UUID | None = None
    tipo_disponibilidade: TipoDisponibilidadeVeiculo | None = None
    unidade: str | None = Field(default=None, max_length=120)
    ativo: bool | None = None
