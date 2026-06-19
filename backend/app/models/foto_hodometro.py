from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UuidPkMixin
from app.models.enums import TipoFotoHodometro, enum_values

if TYPE_CHECKING:
    from app.models.viagem import Viagem


class FotoHodometro(UuidPkMixin, Base):
    __tablename__ = "fotos_hodometro"
    __table_args__ = (
        CheckConstraint("tamanho_bytes > 0", name="ck_fotos_hodometro_tamanho_positivo"),
        Index("ix_fotos_hodometro_viagem_id", "viagem_id"),
    )

    viagem_id: Mapped[UUID] = mapped_column(ForeignKey("viagens.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[TipoFotoHodometro] = mapped_column(
        SqlEnum(TipoFotoHodometro, name="tipo_foto_hodometro", values_callable=enum_values),
        nullable=False,
    )
    arquivo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    viagem: Mapped[Viagem] = relationship(back_populates="fotos_hodometro")

