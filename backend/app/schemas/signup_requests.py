from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    PerfilUsuario,
    StatusSolicitacaoCadastro,
    TipoDisponibilidadeVeiculo,
    TipoVeiculo,
)


class SignupRequestCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: EmailStr
    cargo: str = Field(min_length=1, max_length=150)
    superior: str = Field(min_length=1, max_length=150)
    veiculo_placa: str = Field(min_length=1, max_length=10)
    veiculo_modelo: str = Field(min_length=1, max_length=120)
    veiculo_marca: str = Field(min_length=1, max_length=80)
    observacao: str | None = Field(default=None, max_length=1000)


class SignupRequestApproveRequest(BaseModel):
    senha_temporaria: str = Field(min_length=8, max_length=100)
    perfil: PerfilUsuario = PerfilUsuario.motorista
    superior_id: UUID | None = None
    pode_aprovar: bool = False
    tipo_veiculo: TipoVeiculo = TipoVeiculo.proprio
    tipo_disponibilidade: TipoDisponibilidadeVeiculo | None = None


class SignupRequestRejectRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=1000)


class SignupRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    email: str
    cargo: str
    superior: str
    veiculo_placa: str
    veiculo_modelo: str
    veiculo_marca: str
    observacao: str | None = None
    status: StatusSolicitacaoCadastro
    usuario_id: UUID | None = None
    veiculo_id: UUID | None = None
    processado_por_id: UUID | None = None
    processado_em: datetime | None = None
    motivo_recusa: str | None = None
    criado_em: datetime
    atualizado_em: datetime
