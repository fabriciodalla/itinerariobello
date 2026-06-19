"""adiciona superiores e dados das planilhas

Revision ID: 20260514_0002
Revises: 20260514_0001
Create Date: 2026-05-14 11:35:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260514_0002"
down_revision = "20260514_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("cargo", sa.String(length=150), nullable=True))
    op.add_column("usuarios", sa.Column("superior_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("usuarios", sa.Column("pode_aprovar", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_foreign_key(
        "fk_usuarios_superior_id_usuarios",
        "usuarios",
        "usuarios",
        ["superior_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_usuarios_superior_id", "usuarios", ["superior_id"])

    op.add_column("veiculos", sa.Column("unidade", sa.String(length=120), nullable=True))
    op.add_column("veiculos", sa.Column("categoria", sa.String(length=120), nullable=True))

    op.drop_index("ix_aprovacoes_supervisor_id", table_name="aprovacoes")
    op.drop_constraint("fk_aprovacoes_supervisor_id_usuarios", "aprovacoes", type_="foreignkey")
    op.alter_column(
        "aprovacoes",
        "supervisor_id",
        new_column_name="aprovador_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_aprovacoes_aprovador_id_usuarios",
        "aprovacoes",
        "usuarios",
        ["aprovador_id"],
        ["id"],
    )
    op.create_index("ix_aprovacoes_aprovador_id", "aprovacoes", ["aprovador_id"])


def downgrade() -> None:
    op.drop_index("ix_aprovacoes_aprovador_id", table_name="aprovacoes")
    op.drop_constraint("fk_aprovacoes_aprovador_id_usuarios", "aprovacoes", type_="foreignkey")
    op.alter_column(
        "aprovacoes",
        "aprovador_id",
        new_column_name="supervisor_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_aprovacoes_supervisor_id_usuarios",
        "aprovacoes",
        "usuarios",
        ["supervisor_id"],
        ["id"],
    )
    op.create_index("ix_aprovacoes_supervisor_id", "aprovacoes", ["supervisor_id"])

    op.drop_column("veiculos", "categoria")
    op.drop_column("veiculos", "unidade")

    op.drop_index("ix_usuarios_superior_id", table_name="usuarios")
    op.drop_constraint("fk_usuarios_superior_id_usuarios", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "pode_aprovar")
    op.drop_column("usuarios", "superior_id")
    op.drop_column("usuarios", "cargo")
