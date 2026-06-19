import pytest
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="modelo_dados",
    referencias=("RN-002", "RN-011", "RN-014", "RN-017"),
)
def test_schema_inicial_possui_tabelas_relacionamentos_e_restricoes():
    engine = create_engine(get_settings().database_url)
    inspector = inspect(engine)

    tabelas = set(inspector.get_table_names(schema="public"))
    assert {
        "usuarios",
        "veiculos",
        "viagens",
        "fotos_hodometro",
        "localizacoes_gps",
        "fechamentos_mensais",
        "password_reset_tokens",
        "solicitacoes_cadastro",
    }.issubset(tabelas)

    colunas_veiculos = {coluna["name"] for coluna in inspector.get_columns("veiculos")}
    assert {"marca", "tipo_disponibilidade", "usuario_responsavel_id", "unidade", "categoria", "ativo"}.issubset(
        colunas_veiculos
    )

    colunas_usuarios = {coluna["name"] for coluna in inspector.get_columns("usuarios")}
    assert {"cargo", "superior_id", "pode_aprovar"}.issubset(colunas_usuarios)

    fks_veiculos = inspector.get_foreign_keys("veiculos")
    assert any(fk["referred_table"] == "usuarios" for fk in fks_veiculos)

    checks_veiculos = {check["name"] for check in inspector.get_check_constraints("veiculos")}
    assert "ck_veiculos_fixo_exige_usuario" in checks_veiculos

    fks_viagens = inspector.get_foreign_keys("viagens")
    assert {fk["referred_table"] for fk in fks_viagens} == {"usuarios", "veiculos"}

    colunas_gps = {coluna["name"] for coluna in inspector.get_columns("localizacoes_gps")}
    assert {"latitude", "longitude", "precisao_metros", "endereco", "capturado_em"}.issubset(colunas_gps)

    checks_viagens = {check["name"] for check in inspector.get_check_constraints("viagens")}
    assert "ck_viagens_km_final_maior_igual_inicial" in checks_viagens

    colunas_fechamentos = {coluna["name"] for coluna in inspector.get_columns("fechamentos_mensais")}
    assert {
        "motorista_id",
        "superior_id",
        "ano",
        "mes",
        "status",
        "observacao",
        "avaliado_em",
    }.issubset(colunas_fechamentos)

    checks_fechamentos = {check["name"] for check in inspector.get_check_constraints("fechamentos_mensais")}
    assert "ck_fechamentos_mensais_fechamento_completo" in checks_fechamentos

    fks_fechamentos = inspector.get_foreign_keys("fechamentos_mensais")
    assert {fk["referred_table"] for fk in fks_fechamentos} == {"usuarios"}

    colunas_tokens = {coluna["name"] for coluna in inspector.get_columns("password_reset_tokens")}
    assert {"usuario_id", "token_hash", "expira_em", "usado_em"}.issubset(colunas_tokens)

    colunas_solicitacoes = {coluna["name"] for coluna in inspector.get_columns("solicitacoes_cadastro")}
    assert {
        "nome",
        "email",
        "cargo",
        "superior",
        "veiculo_placa",
        "veiculo_modelo",
        "veiculo_marca",
        "status",
        "usuario_id",
        "veiculo_id",
    }.issubset(colunas_solicitacoes)
