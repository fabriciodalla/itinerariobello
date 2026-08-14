from __future__ import annotations

from uuid import uuid4

import pytest

from assertions import assert_forbidden, assert_validation_error, json_body
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from factories import INVALID_TEXT_FILE, SAMPLE_JPEG, SAMPLE_PDF


def _admin_headers(db) -> tuple[dict[str, str], Usuario]:
    settings = get_settings()
    admin = Usuario(
        nome="Admin Documentos Teste",
        email=f"admin-documentos-{uuid4().hex}@bello.local",
        senha_hash=hash_password("senha-admin-teste"),
        perfil=PerfilUsuario.admin,
    )
    db.add(admin)
    db.commit()
    token = create_access_token(str(admin.id), settings.secret_key, settings.access_token_expire_minutes)
    return {"Authorization": f"Bearer {token}"}, admin


def _motorista_com_veiculo(db) -> tuple[Usuario, Veiculo]:
    suffix = uuid4().hex[:8]
    usuario = Usuario(
        nome="Motorista Documentos Teste",
        email=f"motorista.documentos.{suffix}@bello.local",
        senha_hash=hash_password("senha-motorista-teste"),
        perfil=PerfilUsuario.motorista,
    )
    db.add(usuario)
    db.flush()
    veiculo = Veiculo(
        placa=f"DOC{suffix[:4].upper()}",
        modelo="Veiculo Documentos Teste",
        tipo=TipoVeiculo.proprio,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
        usuario_responsavel_id=usuario.id,
    )
    db.add(veiculo)
    db.commit()
    return usuario, veiculo


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-021", "RN-030"))
def test_admin_anexa_cnh_em_usuario_existente(api_client):
    db = SessionLocal()
    headers, admin = _admin_headers(db)
    usuario, veiculo = _motorista_com_veiculo(db)
    try:
        response = api_client.post(
            f"/users/{usuario.id}/cnh",
            headers=headers,
            files={"arquivo": ("cnh.jpg", SAMPLE_JPEG, "image/jpeg")},
        )

        assert response.status_code == 200, response.text
        data = json_body(response)
        assert data["cnh_download_url"] == f"/users/{usuario.id}/cnh"
        assert data["cnh_arquivo_mime_type"] == "image/jpeg"

        download = api_client.get(f"/users/{usuario.id}/cnh", headers=headers)
        assert download.status_code == 200, download.text
        assert download.content
    finally:
        db.rollback()
        db.delete(db.get(Veiculo, veiculo.id)) if db.get(Veiculo, veiculo.id) else None
        db.delete(db.get(Usuario, usuario.id)) if db.get(Usuario, usuario.id) else None
        db.delete(db.get(Usuario, admin.id)) if db.get(Usuario, admin.id) else None
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-021", "RN-030"))
def test_motorista_nao_pode_anexar_cnh_em_usuario(api_client, motorista_auth_headers):
    db = SessionLocal()
    usuario, veiculo = _motorista_com_veiculo(db)
    try:
        response = api_client.post(
            f"/users/{usuario.id}/cnh",
            headers=motorista_auth_headers,
            files={"arquivo": ("cnh.jpg", SAMPLE_JPEG, "image/jpeg")},
        )

        assert_forbidden(response)
    finally:
        db.rollback()
        db.delete(db.get(Veiculo, veiculo.id)) if db.get(Veiculo, veiculo.id) else None
        db.delete(db.get(Usuario, usuario.id)) if db.get(Usuario, usuario.id) else None
        db.commit()
        db.close()


@pytest.mark.foto
@pytest.mark.risco(peso=20, criticidade="media", area="foto", referencias=("RN-028",))
def test_upload_cnh_rejeita_arquivo_que_nao_e_pdf_nem_imagem(api_client):
    db = SessionLocal()
    headers, admin = _admin_headers(db)
    usuario, veiculo = _motorista_com_veiculo(db)
    try:
        response = api_client.post(
            f"/users/{usuario.id}/cnh",
            headers=headers,
            files={"arquivo": ("cnh.txt", INVALID_TEXT_FILE, "text/plain")},
        )

        assert_validation_error(response)
    finally:
        db.rollback()
        db.delete(db.get(Veiculo, veiculo.id)) if db.get(Veiculo, veiculo.id) else None
        db.delete(db.get(Usuario, usuario.id)) if db.get(Usuario, usuario.id) else None
        db.delete(db.get(Usuario, admin.id)) if db.get(Usuario, admin.id) else None
        db.commit()
        db.close()


@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-021", "RN-030"))
def test_admin_anexa_apolice_em_veiculo_existente_aceitando_pdf(api_client):
    db = SessionLocal()
    headers, admin = _admin_headers(db)
    usuario, veiculo = _motorista_com_veiculo(db)
    try:
        response = api_client.post(
            f"/vehicles/{veiculo.id}/apolice",
            headers=headers,
            files={"arquivo": ("apolice.pdf", SAMPLE_PDF, "application/pdf")},
        )

        assert response.status_code == 200, response.text
        data = json_body(response)
        assert data["apolice_download_url"] == f"/vehicles/{veiculo.id}/apolice"
        assert data["apolice_arquivo_mime_type"] == "application/pdf"

        download = api_client.get(f"/vehicles/{veiculo.id}/apolice", headers=headers)
        assert download.status_code == 200, download.text
        assert download.content
    finally:
        db.rollback()
        db.delete(db.get(Veiculo, veiculo.id)) if db.get(Veiculo, veiculo.id) else None
        db.delete(db.get(Usuario, usuario.id)) if db.get(Usuario, usuario.id) else None
        db.delete(db.get(Usuario, admin.id)) if db.get(Usuario, admin.id) else None
        db.commit()
        db.close()
