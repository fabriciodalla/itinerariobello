from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import limiter
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
from app.services.email import send_password_reset_email
from app.services.password_reset import build_reset_url, create_password_reset_token, reset_password_with_token

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "access_token"


def _set_auth_cookie(response: Response, token: str, max_age_seconds: int) -> None:
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=max_age_seconds,
        domain=settings.cookie_domain,
    )


def _clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
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

    token_response = TokenResponse(access_token=access_token)
    response = Response(
        content=token_response.model_dump_json(),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
    )
    _set_auth_cookie(response, access_token, settings.access_token_expire_minutes * 60)
    return response


@router.get("/me", response_model=UsuarioAutenticadoResponse)
def me(usuario: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: Annotated[Usuario, Depends(get_current_user)]) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_auth_cookie(response)
    return response


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    email = str(payload.email).strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email).where(Usuario.ativo.is_(True)))
    if usuario is None:
        return Response(status_code=status.HTTP_202_ACCEPTED)

    settings = get_settings()
    raw_token = create_password_reset_token(db, usuario, settings)
    reset_url = build_reset_url(settings, raw_token)
    send_password_reset_email(settings, to_email=usuario.email, to_name=usuario.nome, reset_url=reset_url)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Annotated[Session, Depends(get_db)]) -> Response:
    reset_password_with_token(db, token=payload.token, nova_senha=payload.nova_senha)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
