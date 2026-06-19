from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UuidPkMixin
from app.models.enums import AcaoAprovacao, enum_values

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.viagem import Viagem


class Aprovacao(UuidPkMixin, Base):
    __tablename__ = "aprovacoes"
    __table_args__ = (
        CheckConstraint(
            "acao = 'aprovar' OR (observacao IS NOT NULL AND length(btrim(observacao)) > 0)",
            name="ck_aprovacoes_observacao_obrigatoria_reprovacao_ajuste",
        ),
        Index("ix_aprovacoes_viagem_id", "viagem_id"),
        Index("ix_aprovacoes_aprovador_id", "aprovador_id"),
    )

    viagem_id: Mapped[UUID] = mapped_column(ForeignKey("viagens.id", ondelete="CASCADE"), nullable=False)
    aprovador_id: Mapped[UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    acao: Mapped[AcaoAprovacao] = mapped_column(
        SqlEnum(AcaoAprovacao, name="acao_aprovacao", values_callable=enum_values),
        nullable=False,
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    viagem: Mapped[Viagem] = relationship(back_populates="aprovacoes")
    aprovador: Mapped[Usuario] = relationship(back_populates="aprovacoes_realizadas")
