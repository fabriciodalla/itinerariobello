"""adiciona lancamento manual de viagem pelo administrador

Revision ID: 20260917_0015
Revises: 20260901_0014
Create Date: 2026-09-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260917_0015"
down_revision = "20260901_0014"
branch_labels = None
depends_on = None


origem_registro_viagem = postgresql.ENUM(
    "app",
    "manual",
    name="origem_registro_viagem",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    origem_registro_viagem.create(bind, checkfirst=True)

    op.add_column(
        "viagens",
        sa.Column(
            "origem_registro",
            origem_registro_viagem,
            nullable=False,
            server_default="app",
        ),
    )
    op.add_column("viagens", sa.Column("motivo_manual", sa.Text(), nullable=True))
    op.add_column(
        "viagens",
        sa.Column("criado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_viagens_criado_por_id_usuarios",
        "viagens",
        "usuarios",
        ["criado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_viagens_motivo_manual_obrigatorio",
        "viagens",
        "origem_registro <> 'manual' OR motivo_manual IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_viagens_motivo_manual_obrigatorio", "viagens", type_="check")
    op.drop_constraint("fk_viagens_criado_por_id_usuarios", "viagens", type_="foreignkey")
    op.drop_column("viagens", "criado_por_id")
    op.drop_column("viagens", "motivo_manual")
    op.drop_column("viagens", "origem_registro")

    bind = op.get_bind()
    origem_registro_viagem.drop(bind, checkfirst=True)
