"""adiciona recuperacao de senha e solicitacao de cadastro

Revision ID: 20260619_0007
Revises: 20260604_0006
Create Date: 2026-06-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260619_0007"
down_revision = "20260604_0006"
branch_labels = None
depends_on = None


status_solicitacao_cadastro = postgresql.ENUM(
    "pendente",
    "aprovada",
    "rejeitada",
    name="status_solicitacao_cadastro",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    status_solicitacao_cadastro.create(bind, checkfirst=True)

    op.add_column("veiculos", sa.Column("marca", sa.String(length=80), nullable=True))

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_password_reset_tokens_usuario_id_usuarios",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_password_reset_tokens_usuario_id", "password_reset_tokens", ["usuario_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)

    op.create_table(
        "solicitacoes_cadastro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("cargo", sa.String(length=150), nullable=False),
        sa.Column("superior", sa.String(length=150), nullable=False),
        sa.Column("veiculo_placa", sa.String(length=10), nullable=False),
        sa.Column("veiculo_modelo", sa.String(length=120), nullable=False),
        sa.Column("veiculo_marca", sa.String(length=80), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("status", status_solicitacao_cadastro, nullable=False, server_default=sa.text("'pendente'")),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("veiculo_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("processado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("processado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_recusa", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_solicitacoes_cadastro_usuario_id_usuarios",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["veiculo_id"],
            ["veiculos.id"],
            name="fk_solicitacoes_cadastro_veiculo_id_veiculos",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["processado_por_id"],
            ["usuarios.id"],
            name="fk_solicitacoes_cadastro_processado_por_id_usuarios",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_solicitacoes_cadastro_email", "solicitacoes_cadastro", ["email"])
    op.create_index("ix_solicitacoes_cadastro_status", "solicitacoes_cadastro", ["status"])


def downgrade() -> None:
    op.drop_index("ix_solicitacoes_cadastro_status", table_name="solicitacoes_cadastro")
    op.drop_index("ix_solicitacoes_cadastro_email", table_name="solicitacoes_cadastro")
    op.drop_table("solicitacoes_cadastro")

    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_usuario_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_column("veiculos", "marca")

    bind = op.get_bind()
    status_solicitacao_cadastro.drop(bind, checkfirst=True)
