from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario
from app.schemas.usuarios import (
    ResetSenhaAdminRequest,
    UsuarioCreateRequest,
    UsuarioPatchRequest,
    UsuarioResponse,
)

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
