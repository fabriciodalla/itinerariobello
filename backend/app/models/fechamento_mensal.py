from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin
from app.models.enums import StatusFechamentoMensal, enum_values

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class FechamentoMensal(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "fechamentos_mensais"
    __table_args__ = (
        UniqueConstraint("motorista_id", "ano", "mes", name="uq_fechamentos_mensais_motorista_periodo"),
        CheckConstraint("ano >= 2000 AND ano <= 2100", name="ck_fechamentos_mensais_ano_valido"),
        CheckConstraint("mes >= 1 AND mes <= 12", name="ck_fechamentos_mensais_mes_valido"),
        CheckConstraint(
            "status = 'aberto' OR (superior_id IS NOT NULL AND avaliado_em IS NOT NULL)",
            name="ck_fechamentos_mensais_fechamento_completo",
        ),
        Index("ix_fechamentos_mensais_motorista_id", "motorista_id"),
        Index("ix_fechamentos_mensais_superior_id", "superior_id"),
        Index("ix_fechamentos_mensais_periodo", "ano", "mes"),
    )

    motorista_id: Mapped[UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    superior_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusFechamentoMensal] = mapped_column(
        SqlEnum(StatusFechamentoMensal, name="status_fechamento_mensal", values_callable=enum_values),
        nullable=False,
        default=StatusFechamentoMensal.aberto,
        server_default=StatusFechamentoMensal.aberto.value,
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    avaliado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    motorista: Mapped[Usuario] = relationship(
        back_populates="fechamentos_mensais",
        foreign_keys=[motorista_id],
    )
    superior: Mapped[Usuario | None] = relationship(
        back_populates="fechamentos_mensais_avaliados",
        foreign_keys=[superior_id],
    )
