"""padroniza solicitacoes e marcas de veiculos

Revision ID: 20260630_0009
Revises: 20260630_0008
Create Date: 2026-06-30 00:00:00.000000
"""

from alembic import op

revision = "20260630_0009"
down_revision = "20260630_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE veiculos
        SET marca = upper(btrim(regexp_replace(marca, '\\s+', ' ', 'g')))
        WHERE marca IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE solicitacoes_cadastro
        SET veiculo_modelo = upper(btrim(regexp_replace(veiculo_modelo, '^\\s*[^/]+/\\s*', '')))
        WHERE veiculo_modelo IS NOT NULL
          AND veiculo_modelo LIKE '%/%'
        """
    )
    op.execute(
        """
        UPDATE solicitacoes_cadastro
        SET veiculo_modelo = btrim(regexp_replace(
            upper(veiculo_modelo),
            '^(MERCEDES-BENZ|MERCEDES BENZ|VOLKSWAGEN|CHEVROLET|MITSUBISHI|HYUNDAI|RENAULT|TOYOTA|HONDA|FIAT|FORD|JEEP|KIA|NISSAN|PEUGEOT|CITROEN|CITROËN|AUDI|BMW|VOLVO|VW|GM)\\s+',
            ''
        ))
        WHERE veiculo_modelo IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE solicitacoes_cadastro
        SET veiculo_modelo = upper(btrim(regexp_replace(veiculo_modelo, '\\s+', ' ', 'g'))),
            veiculo_marca = upper(btrim(regexp_replace(veiculo_marca, '\\s+', ' ', 'g')))
        """
    )


def downgrade() -> None:
    pass
