"""adiciona cnh de motorista e apolice de seguro de veiculo

Revision ID: 20260813_0010
Revises: 20260630_0009
Create Date: 2026-08-13 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260813_0010"
down_revision = "20260630_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("cnh_arquivo_path", sa.String(length=500), nullable=True))
    op.add_column("usuarios", sa.Column("cnh_arquivo_mime_type", sa.String(length=100), nullable=True))
    op.add_column("usuarios", sa.Column("cnh_arquivo_tamanho_bytes", sa.Integer(), nullable=True))
    op.add_column("usuarios", sa.Column("cnh_arquivo_atualizado_em", sa.DateTime(timezone=True), nullable=True))

    op.add_column("veiculos", sa.Column("apolice_arquivo_path", sa.String(length=500), nullable=True))
    op.add_column("veiculos", sa.Column("apolice_arquivo_mime_type", sa.String(length=100), nullable=True))
    op.add_column("veiculos", sa.Column("apolice_arquivo_tamanho_bytes", sa.Integer(), nullable=True))
    op.add_column("veiculos", sa.Column("apolice_arquivo_atualizado_em", sa.DateTime(timezone=True), nullable=True))

    op.add_column("solicitacoes_cadastro", sa.Column("cnh_arquivo_path", sa.String(length=500), nullable=True))
    op.add_column("solicitacoes_cadastro", sa.Column("cnh_arquivo_mime_type", sa.String(length=100), nullable=True))
    op.add_column("solicitacoes_cadastro", sa.Column("cnh_arquivo_tamanho_bytes", sa.Integer(), nullable=True))
    op.add_column("solicitacoes_cadastro", sa.Column("apolice_arquivo_path", sa.String(length=500), nullable=True))
    op.add_column(
        "solicitacoes_cadastro", sa.Column("apolice_arquivo_mime_type", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "solicitacoes_cadastro", sa.Column("apolice_arquivo_tamanho_bytes", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("solicitacoes_cadastro", "apolice_arquivo_tamanho_bytes")
    op.drop_column("solicitacoes_cadastro", "apolice_arquivo_mime_type")
    op.drop_column("solicitacoes_cadastro", "apolice_arquivo_path")
    op.drop_column("solicitacoes_cadastro", "cnh_arquivo_tamanho_bytes")
    op.drop_column("solicitacoes_cadastro", "cnh_arquivo_mime_type")
    op.drop_column("solicitacoes_cadastro", "cnh_arquivo_path")

    op.drop_column("veiculos", "apolice_arquivo_atualizado_em")
    op.drop_column("veiculos", "apolice_arquivo_tamanho_bytes")
    op.drop_column("veiculos", "apolice_arquivo_mime_type")
    op.drop_column("veiculos", "apolice_arquivo_path")

    op.drop_column("usuarios", "cnh_arquivo_atualizado_em")
    op.drop_column("usuarios", "cnh_arquivo_tamanho_bytes")
    op.drop_column("usuarios", "cnh_arquivo_mime_type")
    op.drop_column("usuarios", "cnh_arquivo_path")
