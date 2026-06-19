import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import select

from assertions import assert_unauthorized, assert_validation_error, json_body
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario
from app.services.password_reset import hash_reset_token


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-001", "RNF-002"))
def test_login_valido_retorna_token(motorista_auth_headers):
    assert motorista_auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-001", "RNF-002"))
def test_login_com_credenciais_invalidas_retorna_401(api_client):
    response = api_client.post(
        "/auth/login",
        json={"email": "usuario.inexistente@bello.local", "senha": "senha-invalida"},
    )

    assert_unauthorized(response)


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-001", "RNF-002"))
def test_login_sem_senha_retorna_erro_de_validacao(api_client):
    response = api_client.post("/auth/login", json={"email": "motorista.teste@bello.local"})

    assert_validation_error(response)


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-003", "RNF-002"))
def test_auth_me_retorna_usuario_autenticado(api_client, motorista_auth_headers):
    response = api_client.get("/auth/me", headers=motorista_auth_headers)

    assert response.status_code == 200, response.text
    data = json_body(response)
    assert isinstance(data, dict)
    assert data.get("email")
    assert data.get("perfil")


@pytest.mark.autenticacao
@pytest.mark.risco(peso=100, criticidade="critica", area="autenticacao", referencias=("RF-003", "RNF-002"))
def test_auth_me_sem_token_retorna_401(api_client):
    response = api_client.get("/auth/me")

    assert_unauthorized(response)


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-003", "RNF-002"))
def test_logout_autenticado_encerra_requisicao_com_sucesso(api_client, fresh_motorista_auth_headers):
    response = api_client.post("/auth/logout", headers=fresh_motorista_auth_headers)

    assert response.status_code in {200, 204}, response.text


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-002", "RNF-002"))
def test_recuperacao_de_senha_aceita_email_para_inicio_do_fluxo(api_client):
    response = api_client.post(
        "/auth/forgot-password",
        json={"email": "motorista.teste@bello.local"},
    )

    assert response.status_code in {200, 202}, response.text


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-002", "RNF-002"))
def test_recuperacao_de_senha_cria_token_para_usuario_ativo(api_client):
    db = SessionLocal()
    email = f"reset-token-{uuid4().hex}@bello.local"
    usuario = Usuario(
        nome="Usuario Reset Token",
        email=email,
        senha_hash=hash_password("senha-atual-teste"),
        perfil=PerfilUsuario.motorista,
    )
    db.add(usuario)
    db.commit()
    try:
        response = api_client.post("/auth/forgot-password", json={"email": email})

        assert response.status_code == 202, response.text
        token = db.scalar(select(PasswordResetToken).where(PasswordResetToken.usuario_id == usuario.id))
        assert token is not None
        assert token.usado_em is None
    finally:
        db.rollback()
        persisted = db.get(Usuario, usuario.id)
        if persisted is not None:
            db.delete(persisted)
            db.commit()
        db.close()


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-002", "RNF-002"))
def test_recuperacao_de_senha_sem_email_retorna_erro_de_validacao(api_client):
    response = api_client.post("/auth/forgot-password", json={})

    assert_validation_error(response)


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-002", "RNF-002"))
def test_reset_de_senha_sem_token_retorna_erro_de_validacao(api_client):
    response = api_client.post(
        "/auth/reset-password",
        json={"nova_senha": "senha-nova-de-teste"},
    )

    assert_validation_error(response)


@pytest.mark.autenticacao
@pytest.mark.risco(peso=50, criticidade="alta", area="autenticacao", referencias=("RF-002", "RNF-001", "RNF-002"))
def test_reset_de_senha_com_token_valido_altera_senha(api_client):
    db = SessionLocal()
    email = f"reset-senha-{uuid4().hex}@bello.local"
    senha_antiga = "senha-antiga-teste"
    senha_nova = "senha-nova-teste"
    usuario = Usuario(
        nome="Usuario Reset Senha",
        email=email,
        senha_hash=hash_password(senha_antiga),
        perfil=PerfilUsuario.motorista,
    )
    db.add(usuario)
    db.flush()
    raw_token = f"token-{uuid4().hex}"
    token = PasswordResetToken(
        usuario_id=usuario.id,
        token_hash=hash_reset_token(raw_token),
        expira_em=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(token)
    db.commit()
    try:
        response = api_client.post(
            "/auth/reset-password",
            json={"token": raw_token, "nova_senha": senha_nova},
        )

        assert response.status_code == 204, response.text
        login_novo = api_client.post("/auth/login", json={"email": email, "senha": senha_nova})
        assert login_novo.status_code == 200, login_novo.text
        login_antigo = api_client.post("/auth/login", json={"email": email, "senha": senha_antiga})
        assert_unauthorized(login_antigo)
    finally:
        db.rollback()
        persisted = db.get(Usuario, usuario.id)
        if persisted is not None:
            db.delete(persisted)
            db.commit()
        db.close()
