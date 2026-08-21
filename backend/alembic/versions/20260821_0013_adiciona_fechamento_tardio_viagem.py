"""adiciona motivo de fechamento tardio na viagem

Revision ID: 20260821_0013
Revises: 20260817_0012
Create Date: 2026-08-21 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260821_0013"
down_revision = "20260817_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "viagens",
        sa.Column("motivo_fechamento_tardio", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("viagens", "motivo_fechamento_tardio")
