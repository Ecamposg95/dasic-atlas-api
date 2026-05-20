"""One-shot backfill para campos enviada_at / pdf_generado_at / actualizado_en
agregados por la migración 20260519_01.

Reglas:
- enviada_at:        primer QuoteEvent con canal='EMAIL' y estatus='SENT' por orden
                     (QuoteEvent usa orden_id, canal y estatus — no existe columna tipo)
- pdf_generado_at:   now() para cotizaciones convertidas a VTA (estatus != COTIZACION)
- actualizado_en:    fecha_creacion para cualquier fila con NULL
                     (las nuevas filas ya tienen el server_default, esto cubre filas
                     existentes antes de la migración)

Idempotente — solo escribe donde está NULL.
"""

from datetime import datetime, timezone

from sqlalchemy import text

from app.db import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)

        db.execute(text("""
            UPDATE ordenes_venta ov
            SET enviada_at = sub.first_sent
            FROM (
                SELECT orden_id, MIN(creado_en) AS first_sent
                FROM quote_events
                WHERE canal = 'EMAIL'
                  AND estatus = 'SENT'
                GROUP BY orden_id
            ) sub
            WHERE ov.id = sub.orden_id
              AND ov.enviada_at IS NULL
        """))

        db.execute(text("""
            UPDATE ordenes_venta
            SET pdf_generado_at = :now
            WHERE estatus != 'COTIZACION'
              AND pdf_generado_at IS NULL
        """), {"now": now})

        db.execute(text("""
            UPDATE ordenes_venta
            SET actualizado_en = COALESCE(fecha_creacion, :now)
            WHERE actualizado_en IS NULL
        """), {"now": now})

        db.commit()
        print("Backfill quote lifecycle: OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()
