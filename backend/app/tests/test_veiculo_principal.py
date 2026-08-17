from datetime import date
from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.services.veiculos import listar_veiculos_disponiveis_para_partida


@pytest.mark.risco(
    peso=50,
    criticidade="alta",
    area="viagem",
    referencias=("RF-004", "RN-033"),
)
def test_ordenacao_prioriza_principal_depois_outros_proprios_depois_alocados():
    """Quando o usuario tem mais de um veiculo proprio, o principal deve vir
    primeiro, o(s) outro(s) veiculo(s) proprio(s) em seguida e os veiculos
    alocados da empresa por ultimo."""
    db = SessionLocal()
    try:
        usuario = Usuario(
            nome="Usuario Dois Carros Teste",
            email="usuario.doiscarros.teste@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add(usuario)
        db.flush()

        segundo_carro = Veiculo(
            placa="ZZZ9Z99",
            modelo="Segundo Carro",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=usuario.id,
            principal=False,
        )
        carro_principal = Veiculo(
            placa="AAA1A11",
            modelo="Carro Principal",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=usuario.id,
            principal=True,
        )
        alocado_empresa = Veiculo(
            placa="BBB2B22",
            modelo="Alocado Empresa",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        )
        db.add_all([segundo_carro, carro_principal, alocado_empresa])
        db.flush()

        disponiveis = listar_veiculos_disponiveis_para_partida(db, usuario.id, date(2026, 8, 17))
        ids_disponiveis = [veiculo.id for veiculo in disponiveis]

        # os dois veiculos proprios do usuario (unicos com esse usuario_responsavel_id
        # na base) devem vir nas duas primeiras posicoes, principal primeiro
        assert ids_disponiveis[0] == carro_principal.id
        assert ids_disponiveis[1] == segundo_carro.id
        assert alocado_empresa.id in ids_disponiveis
        assert ids_disponiveis.index(alocado_empresa.id) > 1
    finally:
        db.rollback()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(
    peso=20,
    criticidade="media",
    area="modelo_dados",
    referencias=("RN-033",),
)
def test_criar_veiculo_sem_principal_explicito_vira_principal_apenas_no_primeiro(api_client):
    """O primeiro veiculo cadastrado para um usuario vira principal automaticamente
    quando o cadastro nao informa o campo; o segundo veiculo, cadastrado do mesmo
    jeito, nao vira principal (para nao substituir o principal sem intencao)."""
    settings = get_settings()
    db = SessionLocal()
    created_users = []
    created_vehicles = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Veiculo Principal Teste",
            email=f"admin.veiculoprincipal.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        motorista = Usuario(
            nome="Motorista Dois Carros Teste",
            email=f"motorista.doiscarros.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([admin, motorista])
        db.commit()
        created_users.extend([admin, motorista])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        headers = {"Authorization": f"Bearer {token}"}

        primeiro = api_client.post(
            "/vehicles",
            json={
                "placa": f"PR{suffix[:5].upper()}",
                "modelo": "Primeiro Carro",
                "marca": "Marca",
                "tipo": "proprio",
                "usuario_responsavel_id": str(motorista.id),
            },
            headers=headers,
        )
        assert primeiro.status_code == 201, primeiro.text
        primeiro_body = primeiro.json()
        assert primeiro_body["principal"] is True
        created_vehicles.append(primeiro_body["id"])

        segundo = api_client.post(
            "/vehicles",
            json={
                "placa": f"SG{suffix[:5].upper()}",
                "modelo": "Segundo Carro",
                "marca": "Marca",
                "tipo": "proprio",
                "usuario_responsavel_id": str(motorista.id),
            },
            headers=headers,
        )
        assert segundo.status_code == 201, segundo.text
        segundo_body = segundo.json()
        assert segundo_body["principal"] is False
        created_vehicles.append(segundo_body["id"])
    finally:
        db.rollback()
        for vehicle_id in reversed(created_vehicles):
            persisted = db.get(Veiculo, vehicle_id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        for user in reversed(created_users):
            persisted = db.get(Usuario, user.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(
    peso=20,
    criticidade="media",
    area="modelo_dados",
    referencias=("RN-033",),
)
def test_marcar_veiculo_como_principal_desmarca_o_anterior(api_client):
    """No maximo um veiculo principal por usuario responsavel: marcar um novo
    veiculo como principal deve desmarcar automaticamente o anterior."""
    settings = get_settings()
    db = SessionLocal()
    created_users = []
    created_vehicles = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Principal Unico Teste",
            email=f"admin.principalunico.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        motorista = Usuario(
            nome="Motorista Principal Unico Teste",
            email=f"motorista.principalunico.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([admin, motorista])
        db.flush()

        veiculo_a = Veiculo(
            placa=f"PA{suffix[:5].upper()}",
            modelo="Veiculo A",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=motorista.id,
            principal=True,
        )
        veiculo_b = Veiculo(
            placa=f"PB{suffix[:5].upper()}",
            modelo="Veiculo B",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=motorista.id,
            principal=False,
        )
        db.add_all([veiculo_a, veiculo_b])
        db.commit()
        created_users.extend([admin, motorista])
        created_vehicles.extend([veiculo_a, veiculo_b])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.patch(
            f"/vehicles/{veiculo_b.id}",
            json={"principal": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["principal"] is True

        db.expire_all()
        assert db.get(Veiculo, veiculo_b.id).principal is True
        assert db.get(Veiculo, veiculo_a.id).principal is False
    finally:
        db.rollback()
        for vehicle in reversed(created_vehicles):
            persisted = db.get(Veiculo, vehicle.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        for user in reversed(created_users):
            persisted = db.get(Usuario, user.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(
    peso=20,
    criticidade="media",
    area="modelo_dados",
    referencias=("RN-033", "RN-017"),
)
def test_veiculo_principal_exige_usuario_responsavel(api_client):
    """Nao e possivel marcar um veiculo como principal sem usuario responsavel."""
    settings = get_settings()
    db = SessionLocal()
    created_users = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Principal Sem Responsavel Teste",
            email=f"admin.principalsemresp.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        db.add(admin)
        db.commit()
        created_users.append(admin)

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.post(
            "/vehicles",
            json={
                "placa": f"SR{suffix[:5].upper()}",
                "modelo": "Sem Responsavel",
                "marca": "Marca",
                "tipo": "empresa",
                "tipo_disponibilidade": "alocado",
                "principal": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422, response.text
    finally:
        db.rollback()
        for user in reversed(created_users):
            persisted = db.get(Usuario, user.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()
