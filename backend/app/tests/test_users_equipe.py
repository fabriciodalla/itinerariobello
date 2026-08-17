from uuid import UUID, uuid4

import pytest

from assertions import assert_forbidden, response_items
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-016", "RN-031"))
def test_admin_lista_equipe_completa(api_client):
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Equipe Teste",
            email=f"admin.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        fora_da_cadeia = Usuario(
            nome="Motorista Fora Da Cadeia",
            email=f"motorista.fora.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([admin, fora_da_cadeia])
        db.commit()
        created.extend([admin, fora_da_cadeia])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.get("/users/equipe", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        ids = {item["id"] for item in response_items(response)}
        assert str(admin.id) in ids
        assert str(fora_da_cadeia.id) in ids
        for item in response_items(response):
            assert set(item.keys()) == {"id", "nome", "cargo"}
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-016", "RN-031"))
def test_supervisor_lista_apenas_propria_cadeia(api_client):
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        gerente = Usuario(
            nome="Gerente Equipe Teste",
            email=f"gerente.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="GERENTE",
            pode_aprovar=True,
        )
        db.add(gerente)
        db.flush()

        coordenador_local = Usuario(
            nome="Coordenador Equipe Teste",
            email=f"coordenador.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="COORDENADOR LOCAL",
            pode_aprovar=True,
            superior_id=gerente.id,
        )
        db.add(coordenador_local)
        db.flush()

        motorista_subordinado = Usuario(
            nome="Motorista Subordinado Equipe Teste",
            email=f"motorista.subordinado.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            cargo="MOTORISTA",
            superior_id=coordenador_local.id,
        )
        fora_da_cadeia = Usuario(
            nome="Motorista Fora Da Cadeia Equipe Teste",
            email=f"motorista.fora.cadeia.equipe.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([motorista_subordinado, fora_da_cadeia])
        db.commit()
        created.extend([gerente, coordenador_local, motorista_subordinado, fora_da_cadeia])

        token = create_access_token(str(gerente.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.get("/users/equipe", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, response.text
        items = response_items(response)
        ids = {item["id"] for item in items}
        assert ids == {str(gerente.id), str(coordenador_local.id), str(motorista_subordinado.id)}
        assert str(fora_da_cadeia.id) not in ids

        coordenador_item = next(item for item in items if item["id"] == str(coordenador_local.id))
        assert coordenador_item["cargo"] == "COORDENADOR LOCAL"
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RNF-004"))
def test_motorista_nao_lista_equipe(api_client, motorista_auth_headers):
    response = api_client.get("/users/equipe", headers=motorista_auth_headers)

    assert_forbidden(response)


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RN-031"))
def test_editar_cargo_de_gestor_garante_pode_aprovar_mesmo_sem_marcar(api_client):
    """Usuario que tambem dirige (perfil motorista) e recebe um cargo de
    coordenacao/gerencia precisa ganhar acesso a equipe automaticamente,
    mesmo que o formulario de edicao nao marque 'pode aprovar' explicitamente
    (reproduz o cenario real: cargo GERENTE com pode_aprovar preso em False)."""
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Cargo Teste",
            email=f"admin.cargo.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        gerente_motorista = Usuario(
            nome="Gerente Que Dirige Teste",
            email=f"gerente.dirige.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            pode_aprovar=False,
        )
        db.add_all([admin, gerente_motorista])
        db.commit()
        created.extend([admin, gerente_motorista])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.patch(
            f"/users/{gerente_motorista.id}",
            json={"cargo": "GERENTE"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["cargo"] == "GERENTE"
        assert body["perfil"] == "motorista"
        assert body["pode_aprovar"] is True
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RN-020", "RF-014"))
def test_editar_usuario_com_pode_aprovar_explicito_false_nao_e_sobrescrito(api_client):
    """O admin pode desmarcar 'pode aprovar' explicitamente para um supervisor ou
    para quem tem cargo de coordenacao/gerencia; essa escolha explicita deve
    prevalecer e nao pode ser silenciosamente revertida para True (regressao:
    supervisores continuavam com acesso ao fechamento mesmo apos o admin
    desmarcar a opcao)."""
    settings = get_settings()
    db = SessionLocal()
    created = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Pode Aprovar Teste",
            email=f"admin.podeaprovar.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        supervisor = Usuario(
            nome="Supervisor Sem Fechamento Teste",
            email=f"supervisor.semfechamento.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="COORDENADOR REGIONAL",
            pode_aprovar=True,
        )
        db.add_all([admin, supervisor])
        db.commit()
        created.extend([admin, supervisor])

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.patch(
            f"/users/{supervisor.id}",
            json={"pode_aprovar": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["perfil"] == "supervisor"
        assert body["cargo"] == "COORDENADOR REGIONAL"
        assert body["pode_aprovar"] is False

        db.expire_all()
        persistido = db.get(Usuario, supervisor.id)
        assert persistido.pode_aprovar is False
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=50, criticidade="alta", area="permissao", referencias=("RF-016", "RN-031"))
def test_criar_usuario_com_cargo_de_gestor_garante_pode_aprovar(api_client):
    """Mesma garantia no cadastro direto (POST /users), nao so na edicao."""
    settings = get_settings()
    db = SessionLocal()
    created_ids = []
    try:
        suffix = uuid4().hex[:6]
        admin = Usuario(
            nome="Admin Cargo Criacao Teste",
            email=f"admin.cargo.criacao.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        db.add(admin)
        db.commit()
        created_ids.append(admin.id)

        token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
        response = api_client.post(
            "/users",
            json={
                "nome": "Coordenador Que Dirige Teste",
                "email": f"coordenador.dirige.{suffix}@belloalimentos.com.br",
                "senha": "senha12345",
                "perfil": "motorista",
                "cargo": "COORDENADOR REGIONAL",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["perfil"] == "motorista"
        assert body["pode_aprovar"] is True
        created_ids.append(UUID(body["id"]))
    finally:
        db.rollback()
        for user_id in reversed(created_ids):
            persisted = db.get(Usuario, user_id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()
