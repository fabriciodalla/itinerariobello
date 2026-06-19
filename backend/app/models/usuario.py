from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin
from app.models.enums import PerfilUsuario, enum_values

if TYPE_CHECKING:
    from app.models.aprovacao import Aprovacao
    from app.models.fechamento_mensal import FechamentoMensal
    from app.models.veiculo import Veiculo
    from app.models.viagem import Viagem


class Usuario(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuarios_email"),
        Index("ix_usuarios_superior_id", "superior_id"),
    )

    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    superior_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    perfil: Mapped[PerfilUsuario] = mapped_column(
        SqlEnum(PerfilUsuario, name="perfil_usuario", values_callable=enum_values),
        nullable=False,
    )
    pode_aprovar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    @property
    def e_aprovador(self) -> bool:
        """Retorna True se o usuario tem permissao de supervisor — seja pelo campo pode_aprovar ou pelo perfil supervisor."""
        return self.pode_aprovar or self.perfil == PerfilUsuario.supervisor

    superior: Mapped[Usuario | None] = relationship(remote_side="Usuario.id", back_populates="subordinados")
    subordinados: Mapped[list[Usuario]] = relationship(back_populates="superior")
    veiculos_responsaveis: Mapped[list[Veiculo]] = relationship(back_populates="usuario_responsavel")
    viagens: Mapped[list[Viagem]] = relationship(back_populates="usuario")
    aprovacoes_realizadas: Mapped[list[Aprovacao]] = relationship(back_populates="aprovador")
    fechamentos_mensais: Mapped[list[FechamentoMensal]] = relationship(
        back_populates="motorista",
        foreign_keys="FechamentoMensal.motorista_id",
    )
    fechamentos_mensais_avaliados: Mapped[list[FechamentoMensal]] = relationship(
        back_populates="superior",
        foreign_keys="FechamentoMensal.superior_id",
    )
