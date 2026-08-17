"""adiciona veiculo principal por usuario responsavel

Revision ID: 20260817_0012
Revises: 20260813_0011
Create Date: 2026-08-17 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260817_0012"
down_revision = "20260813_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "veiculos",
        sa.Column("principal", sa.Boolean(), nullable=False, server_default="false"),
    )
    # No maximo um veiculo principal por usuario responsavel
    op.create_index(
        "uq_veiculos_principal_por_usuario",
        "veiculos",
        ["usuario_responsavel_id"],
        unique=True,
        postgresql_where=sa.text("principal = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_veiculos_principal_por_usuario", table_name="veiculos")
    op.drop_column("veiculos", "principal")
