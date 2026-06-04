"""Config efectiva = defaults de env (get_settings) + overrides de platform_config (DB).
Whitelist estricta de claves editables. Lectura por-llamada (endpoints no son hot)."""
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app import models
from app.core.config import get_settings

EDITABLE_KEYS = {"iva_rate", "quote_validity_days"}


def _overrides(db: Session) -> dict:
    rows = db.query(models.PlatformConfig).filter(models.PlatformConfig.clave.in_(EDITABLE_KEYS)).all()
    return {r.clave: r.valor for r in rows if r.valor is not None}


def get_iva_rate(db: Session) -> Decimal:
    ov = _overrides(db).get("iva_rate")
    if ov is not None:
        try:
            return Decimal(str(ov))
        except (InvalidOperation, ValueError):
            pass
    return Decimal(str(get_settings().iva_rate))


def get_quote_validity_days(db: Session) -> int:
    ov = _overrides(db).get("quote_validity_days")
    if ov is not None:
        try:
            return int(ov)
        except (ValueError, TypeError):
            pass
    return int(get_settings().quote_validity_days)


def effective_summary(db: Session) -> list:
    """Para el GET de la consola: clave, valor efectivo, default, overrideado."""
    s = get_settings()
    ov = _overrides(db)
    return [
        {"clave": "iva_rate", "valor_efectivo": float(get_iva_rate(db)), "default": float(s.iva_rate), "overrideado": "iva_rate" in ov},
        {"clave": "quote_validity_days", "valor_efectivo": get_quote_validity_days(db), "default": int(s.quote_validity_days), "overrideado": "quote_validity_days" in ov},
    ]
