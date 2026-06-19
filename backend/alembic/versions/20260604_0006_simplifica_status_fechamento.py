"""simplifica status de viagem e fechamento mensal

Revision ID: 20260604_0006
Revises: 20260518_0005
Create Date: 2026-06-04 00:00:00.000000
"""

from alembic import op

revision = "20260604_0006"
down_revision = "20260518_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_fechamentos_mensais_observacao_reprovacao",
        "fechamentos_mensais",
        type_="check",
    )
    op.drop_constraint(
        "ck_fechamentos_mensais_avaliacao_completa",
        "fechamentos_mensais",
        type_="check",
    )

    op.execute("ALTER TABLE viagens ALTER COLUMN status DROP DEFAULT")
    op.execute("CREATE TYPE status_viagem_new AS ENUM ('em_andamento', 'concluida')")
    op.execute(
        """
        ALTER TABLE viagens
        ALTER COLUMN status TYPE status_viagem_new
        USING (
            CASE status::text
                WHEN 'rascunho' THEN 'em_andamento'
                WHEN 'em_andamento' THEN 'em_andamento'
                ELSE 'concluida'
            END
        )::status_viagem_new
        """
    )
    op.execute("DROP TYPE status_viagem")
    op.execute("ALTER TYPE status_viagem_new RENAME TO status_viagem")
    op.execute("ALTER TABLE viagens ALTER COLUMN status SET DEFAULT 'em_andamento'::status_viagem")

    op.execute("ALTER TABLE fechamentos_mensais ALTER COLUMN status DROP DEFAULT")
    op.execute("CREATE TYPE status_fechamento_mensal_new AS ENUM ('aberto', 'fechado')")
    op.execute(
        """
        ALTER TABLE fechamentos_mensais
        ALTER COLUMN status TYPE status_fechamento_mensal_new
        USING (
            CASE status::text
                WHEN 'pendente' THEN 'aberto'
                ELSE 'fechado'
            END
        )::status_fechamento_mensal_new
        """
    )
    op.execute("DROP TYPE status_fechamento_mensal")
    op.execute("ALTER TYPE status_fechamento_mensal_new RENAME TO status_fechamento_mensal")
    op.execute("ALTER TABLE fechamentos_mensais ALTER COLUMN status SET DEFAULT 'aberto'::status_fechamento_mensal")

    op.create_check_constraint(
        "ck_fechamentos_mensais_fechamento_completo",
        "fechamentos_mensais",
        "status = 'aberto' OR (superior_id IS NOT NULL AND avaliado_em IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_fechamentos_mensais_fechamento_completo",
        "fechamentos_mensais",
        type_="check",
    )

    op.execute("ALTER TABLE fechamentos_mensais ALTER COLUMN status DROP DEFAULT")
    op.execute("CREATE TYPE status_fechamento_mensal_old AS ENUM ('pendente', 'aprovado', 'reprovado')")
    op.execute(
        """
        ALTER TABLE fechamentos_mensais
        ALTER COLUMN status TYPE status_fechamento_mensal_old
        USING (
            CASE status::text
                WHEN 'aberto' THEN 'pendente'
                ELSE 'aprovado'
            END
        )::status_fechamento_mensal_old
        """
    )
    op.execute("DROP TYPE status_fechamento_mensal")
    op.execute("ALTER TYPE status_fechamento_mensal_old RENAME TO status_fechamento_mensal")
    op.execute("ALTER TABLE fechamentos_mensais ALTER COLUMN status SET DEFAULT 'pendente'::status_fechamento_mensal")

    op.execute("ALTER TABLE viagens ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "CREATE TYPE status_viagem_old AS ENUM "
        "('rascunho', 'em_andamento', 'concluida', 'aprovada', 'reprovada')"
    )
    op.execute(
        """
        ALTER TABLE viagens
        ALTER COLUMN status TYPE status_viagem_old
        USING status::text::status_viagem_old
        """
    )
    op.execute("DROP TYPE status_viagem")
    op.execute("ALTER TYPE status_viagem_old RENAME TO status_viagem")
    op.execute("ALTER TABLE viagens ALTER COLUMN status SET DEFAULT 'em_andamento'::status_viagem")

    op.create_check_constraint(
        "ck_fechamentos_mensais_observacao_reprovacao",
        "fechamentos_mensais",
        "status != 'reprovado' OR (observacao IS NOT NULL AND length(btrim(observacao)) > 0)",
    )
    op.create_check_constraint(
        "ck_fechamentos_mensais_avaliacao_completa",
        "fechamentos_mensais",
        "status = 'pendente' OR (superior_id IS NOT NULL AND avaliado_em IS NOT NULL)",
    )
