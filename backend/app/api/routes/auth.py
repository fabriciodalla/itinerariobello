from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UsuarioAutenticadoResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    email = str(payload.email).strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))

    if usuario is None or not usuario.ativo or not verify_password(payload.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    access_token = create_access_token(str(usuario.id), settings.secret_key, settings.access_token_expire_minutes)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UsuarioAutenticadoResponse)
def me(usuario: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: Annotated[Usuario, Depends(get_current_user)]) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(_: ForgotPasswordRequest) -> Response:
    # No prototipo, o envio de e-mail ainda nao esta integrado; a resposta generica evita enumerar usuarios.
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(_: ResetPasswordRequest) -> Response:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token de recuperacao invalido ou expirado.",
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    if not verify_password(payload.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta.",
        )
    if payload.nova_senha == payload.senha_atual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova senha deve ser diferente da senha atual.",
        )
    usuario.senha_hash = hash_password(payload.nova_senha)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
