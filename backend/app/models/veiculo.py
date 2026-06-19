from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Enum as SqlEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin
from app.models.enums import TipoDisponibilidadeVeiculo, TipoVeiculo, enum_values

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.viagem import Viagem


class Veiculo(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "veiculos"
    __table_args__ = (
        CheckConstraint(
            "tipo_disponibilidade != 'fixo' OR usuario_responsavel_id IS NOT NULL",
            name="ck_veiculos_fixo_exige_usuario",
        ),
        UniqueConstraint("placa", name="uq_veiculos_placa"),
        Index("ix_veiculos_usuario_responsavel_id", "usuario_responsavel_id"),
    )

    placa: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    modelo: Mapped[str] = mapped_column(String(120), nullable=False)
    marca: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo: Mapped[TipoVeiculo] = mapped_column(
        SqlEnum(TipoVeiculo, name="tipo_veiculo", values_callable=enum_values),
        nullable=False,
    )
    tipo_disponibilidade: Mapped[TipoDisponibilidadeVeiculo] = mapped_column(
        SqlEnum(
            TipoDisponibilidadeVeiculo,
            name="tipo_disponibilidade_veiculo",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    usuario_responsavel_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    usuario_responsavel: Mapped[Usuario | None] = relationship(back_populates="veiculos_responsaveis")
    viagens: Mapped[list[Viagem]] = relationship(back_populates="veiculo")
