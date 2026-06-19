import pytest

from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.scripts.importar_planilhas import cargo_permite_aprovacao, perfil_por_cargo, status_para_tipo_e_disponibilidade


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="permissao",
    referencias=("RF-004", "RN-019", "RN-020"),
)
def test_regras_de_importacao_separam_motorista_de_aprovador():
    assert perfil_por_cargo("Supervisor Comercial") == PerfilUsuario.motorista
    assert perfil_por_cargo("Coordenador Comercial") == PerfilUsuario.motorista
    assert cargo_permite_aprovacao("Supervisor Comercial") is False
    assert cargo_permite_aprovacao("Coordenador Comercial") is True
    assert cargo_permite_aprovacao("Gerente Regional") is True


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-016", "RN-017"),
)
def test_status_da_planilha_define_compartilhamento_do_veiculo():
    assert status_para_tipo_e_disponibilidade("empresa") == (
        TipoVeiculo.empresa,
        TipoDisponibilidadeVeiculo.alocado,
    )
    assert status_para_tipo_e_disponibilidade("próprio") == (
        TipoVeiculo.proprio,
        TipoDisponibilidadeVeiculo.fixo,
    )

