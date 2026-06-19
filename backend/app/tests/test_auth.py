import pytest

from assertions import assert_unauthorized, assert_validation_error, json_body


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
