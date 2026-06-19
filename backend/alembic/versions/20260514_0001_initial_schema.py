"""cria schema inicial

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260514_0001"
down_revision = None
branch_labels = None
depends_on = None


perfil_usuario = postgresql.ENUM(
    "motorista",
    "supervisor",
    "analista",
    "admin",
    name="perfil_usuario",
    create_type=False,
)
tipo_veiculo = postgresql.ENUM(
    "proprio",
    "alugado",
    "empresa",
    name="tipo_veiculo",
    create_type=False,
)
tipo_disponibilidade_veiculo = postgresql.ENUM(
    "fixo",
    "alocado",
    name="tipo_disponibilidade_veiculo",
    create_type=False,
)
status_viagem = postgresql.ENUM(
    "rascunho",
    "em_andamento",
    "aguardando_aprovacao",
    "ajuste_solicitado",
    "aprovada",
    "reprovada",
    name="status_viagem",
    create_type=False,
)
tipo_foto_hodometro = postgresql.ENUM(
    "inicial",
    "final",
    name="tipo_foto_hodometro",
    create_type=False,
)
tipo_localizacao_gps = postgresql.ENUM(
    "partida",
    "chegada",
    name="tipo_localizacao_gps",
    create_type=False,
)
acao_aprovacao = postgresql.ENUM(
    "aprovar",
    "reprovar",
    "solicitar_ajuste",
    name="acao_aprovacao",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    perfil_usuario.create(bind, checkfirst=True)
    tipo_veiculo.create(bind, checkfirst=True)
    tipo_disponibilidade_veiculo.create(bind, checkfirst=True)
    status_viagem.create(bind, checkfirst=True)
    tipo_foto_hodometro.create(bind, checkfirst=True)
    tipo_localizacao_gps.create(bind, checkfirst=True)
    acao_aprovacao.create(bind, checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("perfil", perfil_usuario, nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "veiculos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("placa", sa.String(length=10), nullable=False),
        sa.Column("modelo", sa.String(length=120), nullable=False),
        sa.Column("tipo", tipo_veiculo, nullable=False),
        sa.Column("tipo_disponibilidade", tipo_disponibilidade_veiculo, nullable=False),
        sa.Column("usuario_responsavel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "tipo_disponibilidade != 'fixo' OR usuario_responsavel_id IS NOT NULL",
            name="ck_veiculos_fixo_exige_usuario",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_responsavel_id"],
            ["usuarios.id"],
            name="fk_veiculos_usuario_responsavel_id_usuarios",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("placa", name="uq_veiculos_placa"),
    )
    op.create_index("ix_veiculos_placa", "veiculos", ["placa"], unique=True)
    op.create_index("ix_veiculos_usuario_responsavel_id", "veiculos", ["usuario_responsavel_id"])

    op.create_table(
        "viagens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("veiculo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", status_viagem, nullable=False, server_default=sa.text("'em_andamento'")),
        sa.Column("km_inicial", sa.Numeric(12, 2), nullable=False),
        sa.Column("km_final", sa.Numeric(12, 2), nullable=True),
        sa.Column("km_rodado", sa.Numeric(12, 2), nullable=True),
        sa.Column("rota_utilizada", sa.Text(), nullable=True),
        sa.Column("partida_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("chegada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("km_final IS NULL OR km_final >= km_inicial", name="ck_viagens_km_final_maior_igual_inicial"),
        sa.CheckConstraint("km_rodado IS NULL OR km_rodado >= 0", name="ck_viagens_km_rodado_nao_negativo"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_viagens_usuario_id_usuarios"),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"], name="fk_viagens_veiculo_id_veiculos"),
    )
    op.create_index("ix_viagens_usuario_id", "viagens", ["usuario_id"])
    op.create_index("ix_viagens_veiculo_id", "viagens", ["veiculo_id"])
    op.create_index("ix_viagens_status", "viagens", ["status"])

    op.create_table(
        "fotos_hodometro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("viagem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", tipo_foto_hodometro, nullable=False),
        sa.Column("arquivo_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("tamanho_bytes > 0", name="ck_fotos_hodometro_tamanho_positivo"),
        sa.ForeignKeyConstraint(["viagem_id"], ["viagens.id"], name="fk_fotos_hodometro_viagem_id_viagens", ondelete="CASCADE"),
    )
    op.create_index("ix_fotos_hodometro_viagem_id", "fotos_hodometro", ["viagem_id"])

    op.create_table(
        "localizacoes_gps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("viagem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", tipo_localizacao_gps, nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("precisao_metros", sa.Numeric(8, 2), nullable=True),
        sa.Column("capturado_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_localizacoes_gps_latitude_valida"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_localizacoes_gps_longitude_valida"),
        sa.CheckConstraint("precisao_metros IS NULL OR precisao_metros >= 0", name="ck_localizacoes_gps_precisao_nao_negativa"),
        sa.ForeignKeyConstraint(["viagem_id"], ["viagens.id"], name="fk_localizacoes_gps_viagem_id_viagens", ondelete="CASCADE"),
    )
    op.create_index("ix_localizacoes_gps_viagem_id", "localizacoes_gps", ["viagem_id"])

    op.create_table(
        "aprovacoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("viagem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("acao", acao_aprovacao, nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "acao = 'aprovar' OR (observacao IS NOT NULL AND length(btrim(observacao)) > 0)",
            name="ck_aprovacoes_observacao_obrigatoria_reprovacao_ajuste",
        ),
        sa.ForeignKeyConstraint(["viagem_id"], ["viagens.id"], name="fk_aprovacoes_viagem_id_viagens", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supervisor_id"], ["usuarios.id"], name="fk_aprovacoes_supervisor_id_usuarios"),
    )
    op.create_index("ix_aprovacoes_viagem_id", "aprovacoes", ["viagem_id"])
    op.create_index("ix_aprovacoes_supervisor_id", "aprovacoes", ["supervisor_id"])


def downgrade() -> None:
    op.drop_index("ix_aprovacoes_supervisor_id", table_name="aprovacoes")
    op.drop_index("ix_aprovacoes_viagem_id", table_name="aprovacoes")
    op.drop_table("aprovacoes")

    op.drop_index("ix_localizacoes_gps_viagem_id", table_name="localizacoes_gps")
    op.drop_table("localizacoes_gps")

    op.drop_index("ix_fotos_hodometro_viagem_id", table_name="fotos_hodometro")
    op.drop_table("fotos_hodometro")

    op.drop_index("ix_viagens_status", table_name="viagens")
    op.drop_index("ix_viagens_veiculo_id", table_name="viagens")
    op.drop_index("ix_viagens_usuario_id", table_name="viagens")
    op.drop_table("viagens")

    op.drop_index("ix_veiculos_usuario_responsavel_id", table_name="veiculos")
    op.drop_index("ix_veiculos_placa", table_name="veiculos")
    op.drop_table("veiculos")

    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")

    bind = op.get_bind()
    acao_aprovacao.drop(bind, checkfirst=True)
    tipo_localizacao_gps.drop(bind, checkfirst=True)
    tipo_foto_hodometro.drop(bind, checkfirst=True)
    status_viagem.drop(bind, checkfirst=True)
    tipo_disponibilidade_veiculo.drop(bind, checkfirst=True)
    tipo_veiculo.drop(bind, checkfirst=True)
    perfil_usuario.drop(bind, checkfirst=True)

