"""padroniza modelos de veiculos

Revision ID: 20260630_0008
Revises: 20260619_0007
Create Date: 2026-06-30 00:00:00.000000
"""

from alembic import op

revision = "20260630_0008"
down_revision = "20260619_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE veiculos
        SET modelo = upper(btrim(regexp_replace(modelo, '^\\s*[^/]+/\\s*', '')))
        WHERE modelo IS NOT NULL
          AND modelo LIKE '%/%'
        """
    )
    op.execute(
        """
        UPDATE veiculos
        SET modelo = btrim(regexp_replace(
            upper(modelo),
            '^(MERCEDES-BENZ|MERCEDES BENZ|VOLKSWAGEN|CHEVROLET|MITSUBISHI|HYUNDAI|RENAULT|TOYOTA|HONDA|FIAT|FORD|JEEP|KIA|NISSAN|PEUGEOT|CITROEN|CITROËN|AUDI|BMW|VOLVO|VW|GM)\\s+',
            ''
        ))
        WHERE modelo IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE veiculos
        SET modelo = upper(btrim(regexp_replace(modelo, '\\s+', ' ', 'g')))
        WHERE modelo IS NOT NULL
        """
    )


def downgrade() -> None:
    pass
