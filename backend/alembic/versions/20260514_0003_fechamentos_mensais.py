"""adiciona fechamentos mensais por motorista

Revision ID: 20260514_0003
Revises: 20260514_0002
Create Date: 2026-05-14 14:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260514_0003"
down_revision = "20260514_0002"
branch_labels = None
depends_on = None


status_fechamento_mensal = postgresql.ENUM(
    "pendente",
    "aprovado",
    "reprovado",
    name="status_fechamento_mensal",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    status_fechamento_mensal.create(bind, checkfirst=True)

    op.create_table(
        "fechamentos_mensais",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("motorista_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("superior_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("status", status_fechamento_mensal, nullable=False, server_default=sa.text("'pendente'")),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("avaliado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("ano >= 2000 AND ano <= 2100", name="ck_fechamentos_mensais_ano_valido"),
        sa.CheckConstraint("mes >= 1 AND mes <= 12", name="ck_fechamentos_mensais_mes_valido"),
        sa.CheckConstraint(
            "status != 'reprovado' OR (observacao IS NOT NULL AND length(btrim(observacao)) > 0)",
            name="ck_fechamentos_mensais_observacao_reprovacao",
        ),
        sa.CheckConstraint(
            "status = 'pendente' OR (superior_id IS NOT NULL AND avaliado_em IS NOT NULL)",
            name="ck_fechamentos_mensais_avaliacao_completa",
        ),
        sa.ForeignKeyConstraint(["motorista_id"], ["usuarios.id"], name="fk_fechamentos_mensais_motorista_id_usuarios"),
        sa.ForeignKeyConstraint(["superior_id"], ["usuarios.id"], name="fk_fechamentos_mensais_superior_id_usuarios"),
        sa.UniqueConstraint("motorista_id", "ano", "mes", name="uq_fechamentos_mensais_motorista_periodo"),
    )
    op.create_index("ix_fechamentos_mensais_motorista_id", "fechamentos_mensais", ["motorista_id"])
    op.create_index("ix_fechamentos_mensais_superior_id", "fechamentos_mensais", ["superior_id"])
    op.create_index("ix_fechamentos_mensais_periodo", "fechamentos_mensais", ["ano", "mes"])


def downgrade() -> None:
    op.drop_index("ix_fechamentos_mensais_periodo", table_name="fechamentos_mensais")
    op.drop_index("ix_fechamentos_mensais_superior_id", table_name="fechamentos_mensais")
    op.drop_index("ix_fechamentos_mensais_motorista_id", table_name="fechamentos_mensais")
    op.drop_table("fechamentos_mensais")

    bind = op.get_bind()
    status_fechamento_mensal.drop(bind, checkfirst=True)
