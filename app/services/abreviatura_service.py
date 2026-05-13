"""Generador de abreviaturas para productos.

Convención: 3 chars de la marca + "-" + 3 chars de la categoría.
- Normaliza acentos (Schneider → SCH, Eléctrico → ELE)
- Solo A-Z (descarta dígitos y símbolos)
- Devuelve "" si no hay datos suficientes
"""

import re
import unicodedata


def _normalizar(texto: str | None) -> str:
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z]", "", s).upper()
    return s


def generar(marca: str | None, categoria: str | None) -> str:
    """Genera 'MAR-CAT' (max 7 chars). Vacío si faltan ambos.

    Ejemplos:
      generar("Schneider", "Relevadores") → "SCH-REL"
      generar("ABB",       "Contactores") → "ABB-CON"
      generar("Siemens",   None)          → "SIE"
      generar(None,        "Sensores")    → "SEN"
      generar(None,        None)          → ""
    """
    m = _normalizar(marca)[:3]
    c = _normalizar(categoria)[:3]
    if m and c:
        return f"{m}-{c}"
    return m or c or ""
