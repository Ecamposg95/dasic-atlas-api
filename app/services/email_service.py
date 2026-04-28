"""
SMTP email service. Configurable via env vars (SMTP_HOST/PORT/USER/PASSWORD/FROM/USE_TLS).
Si SMTP_HOST está vacío, queda en modo "DRY_RUN" y solo registra el evento.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


def smtp_configured() -> bool:
    s = get_settings()
    return bool(s.smtp_host and s.smtp_from)


def send_quote_email(
    *,
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[Iterable[str]] = None,
    pdf_attachment: Optional[tuple[str, bytes]] = None,
) -> str:
    """Devuelve 'SENT' si se envía, 'DRY_RUN' si SMTP no está configurado.
    Lanza EmailDeliveryError ante fallas SMTP."""
    s = get_settings()

    if not smtp_configured():
        logger.warning("SMTP no configurado — DRY_RUN. to=%s subject=%s", to, subject)
        return "DRY_RUN"

    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    if pdf_attachment:
        filename, payload = pdf_attachment
        msg.add_attachment(payload, maintype="application", subtype="pdf", filename=filename)

    try:
        if s.smtp_use_tls and s.smtp_port == 465:
            with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=20) as smtp:
                if s.smtp_user:
                    smtp.login(s.smtp_user, s.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as smtp:
                smtp.ehlo()
                if s.smtp_use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                if s.smtp_user:
                    smtp.login(s.smtp_user, s.smtp_password)
                smtp.send_message(msg)
        return "SENT"
    except (smtplib.SMTPException, OSError) as exc:
        logger.exception("SMTP delivery failed: %s", exc)
        raise EmailDeliveryError(str(exc)) from exc
