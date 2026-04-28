"""
IA service: usa Anthropic Claude para sugerir próximos pasos comerciales
sobre una cotización. Si ANTHROPIC_API_KEY no está, devuelve un resumen
heurístico local sin llamar al modelo.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def ai_configured() -> bool:
    return bool(get_settings().anthropic_api_key)


def _heuristic_summary(quote_dict: dict[str, Any]) -> str:
    edad = quote_dict.get("edad_dias", 0) or 0
    dias_restantes = quote_dict.get("dias_restantes")
    estatus = (quote_dict.get("estatus") or "").lower()
    cliente = quote_dict.get("cliente", "el cliente")
    total = quote_dict.get("total", 0)
    moneda = quote_dict.get("moneda", "MXN")

    bullets: list[str] = []
    bullets.append(f"Cotización {quote_dict.get('folio')} a {cliente} — {moneda} {total}")
    if estatus == "cotizacion":
        if dias_restantes is None:
            bullets.append("Sin fecha de vencimiento; confirmar vigencia con cliente.")
        elif dias_restantes < 0:
            bullets.append(f"VENCIDA hace {abs(dias_restantes)} días — recotizar y enviar nueva versión.")
        elif dias_restantes <= 3:
            bullets.append(f"Por vencer en {dias_restantes} días — agendar llamada de cierre HOY.")
        elif edad > 7:
            bullets.append(f"Sin actividad en {edad} días — enviar follow-up por WhatsApp/correo.")
        else:
            bullets.append("En periodo de seguimiento normal — confirmar dudas técnicas.")
    elif estatus == "pendiente":
        bullets.append("Venta confirmada — coordinar pago y entrega con almacén.")
    elif estatus == "pagada":
        bullets.append("Pagada — pedir reseña / referidos.")

    return "Sugerencias (modo heurístico, sin IA):\n- " + "\n- ".join(bullets)


def sugerir_proximo_paso(quote_dict: dict[str, Any]) -> dict[str, Any]:
    """Devuelve {'modo': 'IA'|'HEURISTICO', 'resumen': str}."""
    if not ai_configured():
        return {"modo": "HEURISTICO", "resumen": _heuristic_summary(quote_dict)}

    try:
        # Import lazy: solo si la API key está presente
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        logger.warning("anthropic SDK no instalado — fallback a heurístico")
        return {"modo": "HEURISTICO", "resumen": _heuristic_summary(quote_dict)}

    s = get_settings()
    client = Anthropic(api_key=s.anthropic_api_key)

    folio = quote_dict.get("folio")
    cliente = quote_dict.get("cliente")
    total = quote_dict.get("total")
    moneda = quote_dict.get("moneda")
    edad = quote_dict.get("edad_dias")
    dias_restantes = quote_dict.get("dias_restantes")
    estatus = quote_dict.get("estatus")
    detalles = quote_dict.get("detalles_resumen", "")

    user_prompt = f"""Eres un asesor comercial industrial B2B (DASIC).
Analiza esta cotización y sugiere el próximo paso concreto y accionable
para cerrar la venta. Responde en español, máximo 4 bullets, directo.

Folio: {folio}
Cliente: {cliente}
Total: {moneda} {total}
Estatus: {estatus}
Edad (días): {edad}
Días restantes vigencia: {dias_restantes}
Detalles: {detalles}

Devuelve solo el plan de acción en bullets."""

    try:
        resp = client.messages.create(
            model=s.anthropic_model,
            max_tokens=400,
            messages=[{"role": "user", "content": user_prompt}],
        )
        texto = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()
        if not texto:
            texto = _heuristic_summary(quote_dict)
            return {"modo": "HEURISTICO", "resumen": texto}
        return {"modo": "IA", "resumen": texto, "model": s.anthropic_model}
    except Exception as exc:  # pragma: no cover
        logger.exception("Fallo IA Anthropic: %s", exc)
        return {"modo": "HEURISTICO", "resumen": _heuristic_summary(quote_dict)}
