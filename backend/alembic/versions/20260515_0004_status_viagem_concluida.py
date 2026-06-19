"""renomeia status_viagem: aguardando_aprovacao e ajuste_solicitado -> concluida

Revision ID: 20260515_0004
Revises: 20260514_0003
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op

revision = "20260515_0004"
down_revision = "20260514_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cria novo tipo sem os valores obsoletos
    op.execute("CREATE TYPE status_viagem_new AS ENUM ('rascunho', 'em_andamento', 'concluida', 'aprovada', 'reprovada')")

    # Remove o server_default antes de trocar o tipo (ele usa o tipo antigo)
    op.execute("ALTER TABLE viagens ALTER COLUMN status DROP DEFAULT")

    # Troca o tipo da coluna convertendo aguardando_aprovacao/ajuste_solicitado -> concluida inline
    op.execute(
        """
        ALTER TABLE viagens
        ALTER COLUMN status TYPE status_viagem_new
        USING (
            CASE status::text
                WHEN 'aguardando_aprovacao' THEN 'concluida'
                WHEN 'ajuste_solicitado'    THEN 'concluida'
                ELSE status::text
            END
        )::status_viagem_new
        """
    )

    # Remove tipo antigo e renomeia o novo
    op.execute("DROP TYPE status_viagem")
    op.execute("ALTER TYPE status_viagem_new RENAME TO status_viagem")

    # Restaura o server_default com o novo tipo
    op.execute("ALTER TABLE viagens ALTER COLUMN status SET DEFAULT 'em_andamento'::status_viagem")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE status_viagem_old AS ENUM "
        "('rascunho', 'em_andamento', 'aguardando_aprovacao', 'ajuste_solicitado', 'aprovada', 'reprovada')"
    )
    op.execute(
        "UPDATE viagens SET status = 'aguardando_aprovacao' WHERE status = 'concluida'"
    )
    op.execute(
        "ALTER TABLE viagens "
        "ALTER COLUMN status TYPE status_viagem_old "
        "USING status::text::status_viagem_old"
    )
    op.execute("DROP TYPE status_viagem")
    op.execute("ALTER TYPE status_viagem_old RENAME TO status_viagem")
