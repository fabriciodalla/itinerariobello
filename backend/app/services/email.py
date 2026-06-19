from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import Settings

logger = logging.getLogger(__name__)


def send_password_reset_email(settings: Settings, *, to_email: str, to_name: str, reset_url: str) -> bool:
    if not settings.smtp_configured:
        logger.warning("SMTP nao configurado; e-mail de recuperacao de senha nao enviado.")
        return False

    from_email = settings.smtp_from_email or settings.smtp_username
    if not from_email:
        logger.warning("Remetente SMTP nao configurado; e-mail de recuperacao de senha nao enviado.")
        return False

    message = EmailMessage()
    message["Subject"] = "Recuperacao de senha - Itinerario Bello"
    message["From"] = f"{settings.smtp_from_name} <{from_email}>"
    message["To"] = to_email
    message.set_content(
        "\n".join(
            [
                f"Ola, {to_name}.",
                "",
                "Use o link abaixo para definir uma nova senha:",
                reset_url,
                "",
                f"O link expira em {settings.password_reset_token_expire_minutes} minutos.",
                "Se voce nao solicitou a recuperacao, ignore este e-mail.",
            ]
        )
    )

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                _authenticate_and_send(settings, smtp, message)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                _authenticate_and_send(settings, smtp, message)
    except OSError:
        logger.exception("Falha ao enviar e-mail de recuperacao de senha.")
        return False

    return True


def _authenticate_and_send(settings: Settings, smtp: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.smtp_username and settings.smtp_password:
        smtp.login(settings.smtp_username, settings.smtp_password)
    smtp.send_message(message)
