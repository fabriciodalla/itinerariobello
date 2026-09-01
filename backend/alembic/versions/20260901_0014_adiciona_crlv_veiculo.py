"""adiciona crlv de veiculo

Revision ID: 20260901_0014
Revises: 20260821_0013
Create Date: 2026-09-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260901_0014"
down_revision = "20260821_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("veiculos", sa.Column("crlv_arquivo_path", sa.String(length=500), nullable=True))
    op.add_column("veiculos", sa.Column("crlv_arquivo_mime_type", sa.String(length=100), nullable=True))
    op.add_column("veiculos", sa.Column("crlv_arquivo_tamanho_bytes", sa.Integer(), nullable=True))
    op.add_column("veiculos", sa.Column("crlv_arquivo_atualizado_em", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("veiculos", "crlv_arquivo_atualizado_em")
    op.drop_column("veiculos", "crlv_arquivo_tamanho_bytes")
    op.drop_column("veiculos", "crlv_arquivo_mime_type")
    op.drop_column("veiculos", "crlv_arquivo_path")
