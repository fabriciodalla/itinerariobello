from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin
from app.models.enums import StatusSolicitacaoCadastro, enum_values

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.veiculo import Veiculo


class SolicitacaoCadastro(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "solicitacoes_cadastro"
    __table_args__ = (
        Index("ix_solicitacoes_cadastro_email", "email"),
        Index("ix_solicitacoes_cadastro_status", "status"),
    )

    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo: Mapped[str] = mapped_column(String(150), nullable=False)
    superior: Mapped[str] = mapped_column(String(150), nullable=False)
    veiculo_placa: Mapped[str] = mapped_column(String(10), nullable=False)
    veiculo_modelo: Mapped[str] = mapped_column(String(120), nullable=False)
    veiculo_marca: Mapped[str] = mapped_column(String(80), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StatusSolicitacaoCadastro] = mapped_column(
        SqlEnum(
            StatusSolicitacaoCadastro,
            name="status_solicitacao_cadastro",
            values_callable=enum_values,
        ),
        nullable=False,
        default=StatusSolicitacaoCadastro.pendente,
        server_default=StatusSolicitacaoCadastro.pendente.value,
    )
    usuario_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    veiculo_id: Mapped[UUID | None] = mapped_column(ForeignKey("veiculos.id", ondelete="SET NULL"), nullable=True)
    processado_por_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    processado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_recusa: Mapped[str | None] = mapped_column(Text, nullable=True)

    usuario: Mapped[Usuario | None] = relationship(foreign_keys=[usuario_id])
    veiculo: Mapped[Veiculo | None] = relationship()
    processado_por: Mapped[Usuario | None] = relationship(foreign_keys=[processado_por_id])
