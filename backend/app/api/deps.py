from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas ou expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> Usuario:
    raw_token: str | None = None

    if credentials and credentials.scheme.lower() == "bearer":
        raw_token = credentials.credentials
    elif access_token:
        raw_token = access_token

    if raw_token is None:
        raise authentication_error()

    settings = get_settings()
    subject = decode_access_token(raw_token, settings.secret_key)
    if subject is None:
        raise authentication_error()

    try:
        usuario_id = UUID(subject)
    except ValueError as exc:
        raise authentication_error() from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise authentication_error()

    return usuario


def require_admin(usuario: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
    if usuario.perfil != PerfilUsuario.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem permissao para esta acao.",
        )
    return usuario
