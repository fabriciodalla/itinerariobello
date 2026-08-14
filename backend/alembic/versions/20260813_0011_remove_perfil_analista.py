"""remove perfil analista do enum perfil_usuario

Revision ID: 20260813_0011
Revises: 20260813_0010
Create Date: 2026-08-13 15:30:00.000000
"""

from alembic import op

revision = "20260813_0011"
down_revision = "20260813_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ALTER COLUMN perfil DROP DEFAULT")
    op.execute("CREATE TYPE perfil_usuario_new AS ENUM ('motorista', 'supervisor', 'admin')")
    op.execute(
        """
        ALTER TABLE usuarios
        ALTER COLUMN perfil TYPE perfil_usuario_new
        USING (
            CASE perfil::text
                WHEN 'analista' THEN 'supervisor'
                ELSE perfil::text
            END
        )::perfil_usuario_new
        """
    )
    op.execute("DROP TYPE perfil_usuario")
    op.execute("ALTER TYPE perfil_usuario_new RENAME TO perfil_usuario")


def downgrade() -> None:
    op.execute("CREATE TYPE perfil_usuario_old AS ENUM ('motorista', 'supervisor', 'analista', 'admin')")
    op.execute(
        """
        ALTER TABLE usuarios
        ALTER COLUMN perfil TYPE perfil_usuario_old
        USING perfil::text::perfil_usuario_old
        """
    )
    op.execute("DROP TYPE perfil_usuario")
    op.execute("ALTER TYPE perfil_usuario_old RENAME TO perfil_usuario")
