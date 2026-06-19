from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import StatusFechamentoMensal, StatusViagem, TipoFotoHodometro, TipoLocalizacaoGPS
from app.schemas.location import endereco_foi_resolvido, endereco_para_exibicao


class GPSPayload(BaseModel):
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)
    precisao_metros: Decimal | None = Field(default=None, ge=0)
    endereco: str | None = Field(default=None, max_length=500)

    @field_validator("endereco")
    @classmethod
    def limpar_endereco(cls, value: str | None) -> str | None:
        if value is None:
            return None
        endereco = value.strip()
        return endereco or None


class TripStartPayload(BaseModel):
    veiculo_id: UUID
    km_inicial: Decimal = Field(ge=0)
    gps: GPSPayload


class TripFinishPayload(BaseModel):
    km_final: Decimal = Field(ge=0)
    rota_utilizada: str = Field(min_length=1)
    gps: GPSPayload


class TripPatchPayload(BaseModel):
    rota_utilizada: str | None = None
    km_inicial: Decimal | None = Field(default=None, ge=0)
    km_final: Decimal | None = Field(default=None, ge=0)


class MonthlyClosureClosePayload(BaseModel):
    observacao: str | None = None


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    viagem_id: UUID
    tipo: TipoFotoHodometro
    mime_type: str
    tamanho_bytes: int
    criado_em: datetime


class ReportPhotoEvidenceResponse(PhotoResponse):
    download_url: str


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    usuario_nome: str
    veiculo_id: UUID
    veiculo_placa: str
    veiculo_modelo: str
    status: StatusViagem
    km_inicial: Decimal
    km_final: Decimal | None = None
    km_rodado: Decimal | None = None
    rota_utilizada: str | None = None
    partida_em: datetime
    chegada_em: datetime | None = None
    foto_hodometro_inicial: ReportPhotoEvidenceResponse | None = None
    foto_hodometro_final: ReportPhotoEvidenceResponse | None = None


class GPSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    viagem_id: UUID
    tipo: TipoLocalizacaoGPS
    latitude: Decimal
    longitude: Decimal
    precisao_metros: Decimal | None = None
    endereco: str | None = None
    capturado_em: datetime

    @computed_field
    @property
    def endereco_resolvido(self) -> bool:
        return endereco_foi_resolvido(self.endereco)

    @computed_field
    @property
    def endereco_exibicao(self) -> str:
        return endereco_para_exibicao(self.endereco)


class ReportItemResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    usuario_nome: str
    veiculo_id: UUID
    veiculo_placa: str
    veiculo_modelo: str
    partida_em: datetime
    chegada_em: datetime | None
    km_inicial: Decimal
    km_final: Decimal | None
    km_rodado: Decimal | None
    rota_utilizada: str | None
    foto_hodometro_inicial: ReportPhotoEvidenceResponse | None = None
    foto_hodometro_final: ReportPhotoEvidenceResponse | None = None
    gps_partida: GPSResponse | None = None
    gps_chegada: GPSResponse | None = None
    status: StatusViagem
    fechamento_mensal_id: UUID | None = None
    status_fechamento: StatusFechamentoMensal = StatusFechamentoMensal.aberto
    superior_id: UUID | None = None
    avaliado_em: datetime | None = None
    observacao_fechamento: str | None = None


class MonthlyClosureResponse(BaseModel):
    id: UUID | None = None
    motorista_id: UUID
    motorista_nome: str
    ano: int
    mes: int
    status: StatusFechamentoMensal
    superior_id: UUID | None = None
    avaliado_em: datetime | None = None
    observacao: str | None = None
    total_viagens: int
    km_total: Decimal
