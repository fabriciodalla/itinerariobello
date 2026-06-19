from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_reset_url(settings: Settings, token: str) -> str:
    base_url = settings.frontend_base_url.rstrip("/")
    return f"{base_url}/?{urlencode({'reset_token': token})}"


def create_password_reset_token(db: Session, usuario: Usuario, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    tokens_abertos = db.scalars(
        select(PasswordResetToken)
        .where(PasswordResetToken.usuario_id == usuario.id)
        .where(PasswordResetToken.usado_em.is_(None))
    ).all()
    for token_aberto in tokens_abertos:
        token_aberto.usado_em = now

    raw_token = token_urlsafe(32)
    reset_token = PasswordResetToken(
        usuario_id=usuario.id,
        token_hash=hash_reset_token(raw_token),
        expira_em=now + timedelta(minutes=settings.password_reset_token_expire_minutes),
    )
    db.add(reset_token)
    db.commit()
    return raw_token


def reset_password_with_token(db: Session, *, token: str, nova_senha: str) -> None:
    token_hash = hash_reset_token(token)
    reset_token = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)

    expira_em = reset_token.expira_em if reset_token is not None else None
    if expira_em is not None and expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)

    if (
        reset_token is None
        or reset_token.usado_em is not None
        or expira_em is None
        or expira_em <= now
        or reset_token.usuario is None
        or not reset_token.usuario.ativo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperacao invalido ou expirado.",
        )

    reset_token.usuario.senha_hash = hash_password(nova_senha)
    reset_token.usado_em = now
    db.commit()
