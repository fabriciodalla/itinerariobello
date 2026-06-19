from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UuidPkMixin
from app.models.enums import TipoLocalizacaoGPS, enum_values

if TYPE_CHECKING:
    from app.models.viagem import Viagem


class LocalizacaoGPS(UuidPkMixin, Base):
    __tablename__ = "localizacoes_gps"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_localizacoes_gps_latitude_valida"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_localizacoes_gps_longitude_valida"),
        CheckConstraint("precisao_metros IS NULL OR precisao_metros >= 0", name="ck_localizacoes_gps_precisao_nao_negativa"),
        Index("ix_localizacoes_gps_viagem_id", "viagem_id"),
    )

    viagem_id: Mapped[UUID] = mapped_column(ForeignKey("viagens.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[TipoLocalizacaoGPS] = mapped_column(
        SqlEnum(TipoLocalizacaoGPS, name="tipo_localizacao_gps", values_callable=enum_values),
        nullable=False,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    precisao_metros: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    endereco: Mapped[str | None] = mapped_column(Text, nullable=True)
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    viagem: Mapped[Viagem] = relationship(back_populates="localizacoes_gps")
