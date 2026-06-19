from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin
from app.models.enums import StatusViagem, enum_values

if TYPE_CHECKING:
    from app.models.aprovacao import Aprovacao
    from app.models.foto_hodometro import FotoHodometro
    from app.models.localizacao_gps import LocalizacaoGPS
    from app.models.usuario import Usuario
    from app.models.veiculo import Veiculo


class Viagem(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "viagens"
    __table_args__ = (
        CheckConstraint("km_final IS NULL OR km_final >= km_inicial", name="ck_viagens_km_final_maior_igual_inicial"),
        CheckConstraint("km_rodado IS NULL OR km_rodado >= 0", name="ck_viagens_km_rodado_nao_negativo"),
        Index("ix_viagens_usuario_id", "usuario_id"),
        Index("ix_viagens_veiculo_id", "veiculo_id"),
        Index("ix_viagens_status", "status"),
    )

    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    veiculo_id: Mapped[UUID] = mapped_column(ForeignKey("veiculos.id"), nullable=False)
    status: Mapped[StatusViagem] = mapped_column(
        SqlEnum(StatusViagem, name="status_viagem", values_callable=enum_values),
        nullable=False,
        default=StatusViagem.em_andamento,
        server_default=StatusViagem.em_andamento.value,
    )
    km_inicial: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    km_final: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    km_rodado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    rota_utilizada: Mapped[str | None] = mapped_column(Text, nullable=True)
    partida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    chegada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    usuario: Mapped[Usuario] = relationship(back_populates="viagens")
    veiculo: Mapped[Veiculo] = relationship(back_populates="viagens")
    fotos_hodometro: Mapped[list[FotoHodometro]] = relationship(back_populates="viagem")
    localizacoes_gps: Mapped[list[LocalizacaoGPS]] = relationship(back_populates="viagem")
    aprovacoes: Mapped[list[Aprovacao]] = relationship(back_populates="viagem")

