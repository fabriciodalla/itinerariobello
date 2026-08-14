from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.usuarios import (
    ResetSenhaAdminRequest,
    UsuarioCreateRequest,
    UsuarioPatchRequest,
    UsuarioResponse,
    UsuarioResumoResponse,
)
from app.services.documents import cnh_subdir, delete_document_if_exists, save_document
from app.services.hierarchy import collect_subordinate_ids

router = APIRouter(prefix="/users", tags=["users"])


def _get_or_404(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return usuario


@router.get("", response_model=list[UsuarioResponse])
def list_users(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.nome)).all())


@router.get("/equipe", response_model=list[UsuarioResumoResponse])
def list_team_members(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Usuario]:
    """Lista leve (id, nome, cargo) usada para dar contexto de hierarquia em seletores,
    ex.: dropdown de motorista no fechamento mensal. Admin ve todos; responsavel pelo
    fechamento ve a propria cadeia de subordinados (direta e indireta) mais si mesmo."""
    if usuario.perfil != PerfilUsuario.admin and not usuario.pode_aprovar:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para consultar a equipe.")

    if usuario.perfil == PerfilUsuario.admin:
        return list(db.scalars(select(Usuario).order_by(Usuario.nome)).all())

    team_ids = collect_subordinate_ids(db, usuario.id) | {usuario.id}
    return list(db.scalars(select(Usuario).where(Usuario.id.in_(team_ids)).order_by(Usuario.nome)).all())


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UsuarioCreateRequest,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    email = str(payload.email).strip().lower()
    if db.scalar(select(Usuario).where(Usuario.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado.")

    if payload.superior_id is not None and db.get(Usuario, payload.superior_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Superior nao encontrado.",
        )

    pode_aprovar = payload.pode_aprovar or payload.perfil == PerfilUsuario.supervisor
    usuario = Usuario(
        nome=payload.nome.strip(),
        email=email,
        senha_hash=hash_password(payload.senha),
        cargo=payload.cargo.strip() if payload.cargo else None,
        perfil=payload.perfil,
        superior_id=payload.superior_id,
        pode_aprovar=pode_aprovar,
        ativo=payload.ativo,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_user(
    usuario_id: UUID,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    return _get_or_404(db, usuario_id)


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def patch_user(
    usuario_id: UUID,
    payload: UsuarioPatchRequest,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    usuario = _get_or_404(db, usuario_id)
    fields = payload.model_fields_set

    if "email" in fields and payload.email is not None:
        email = str(payload.email).strip().lower()
        if db.scalar(select(Usuario).where(Usuario.email == email).where(Usuario.id != usuario_id)) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado.")
        usuario.email = email

    if "nome" in fields and payload.nome is not None:
        usuario.nome = payload.nome.strip()

    if "cargo" in fields:
        usuario.cargo = payload.cargo.strip() if payload.cargo else None

    if "perfil" in fields and payload.perfil is not None:
        usuario.perfil = payload.perfil
        if payload.perfil == PerfilUsuario.supervisor:
            usuario.pode_aprovar = True

    if "superior_id" in fields:
        if payload.superior_id is not None:
            if payload.superior_id == usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Usuario nao pode ser superior de si mesmo.",
                )
            if db.get(Usuario, payload.superior_id) is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Superior nao encontrado.",
                )
        usuario.superior_id = payload.superior_id

    if "pode_aprovar" in fields and payload.pode_aprovar is not None:
        usuario.pode_aprovar = payload.pode_aprovar

    if "ativo" in fields and payload.ativo is not None:
        usuario.ativo = payload.ativo

    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/{usuario_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_password(
    usuario_id: UUID,
    payload: ResetSenhaAdminRequest,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    usuario = _get_or_404(db, usuario_id)
    usuario.senha_hash = hash_password(payload.nova_senha)
    db.commit()


@router.post("/{usuario_id}/cnh", response_model=UsuarioResponse)
def upload_user_cnh(
    usuario_id: UUID,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    arquivo: UploadFile,
) -> Usuario:
    usuario = _get_or_404(db, usuario_id)
    settings = get_settings()
    arquivo_path, tamanho_bytes, mime_type = save_document(
        arquivo, settings.photos_dir, cnh_subdir(usuario.id), "cnh"
    )
    arquivo_anterior = usuario.cnh_arquivo_path
    usuario.cnh_arquivo_path = arquivo_path
    usuario.cnh_arquivo_mime_type = mime_type
    usuario.cnh_arquivo_tamanho_bytes = tamanho_bytes
    usuario.cnh_arquivo_atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    delete_document_if_exists(arquivo_anterior)
    return usuario


@router.get("/{usuario_id}/cnh")
def download_user_cnh(
    usuario_id: UUID,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    usuario = _get_or_404(db, usuario_id)
    if not usuario.cnh_arquivo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNH nao cadastrada para este usuario.")
    path = Path(usuario.cnh_arquivo_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo da CNH nao encontrado.")
    return FileResponse(path, media_type=usuario.cnh_arquivo_mime_type)
