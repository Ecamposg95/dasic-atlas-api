-- ============================================================================
-- DEDUP DE EMPRESAS DUPLICADAS (mismo RFC) — DASIC Atlas
-- ============================================================================
-- ⚠️  DESTRUCTIVO. Corre contra PRODUCCIÓN. Lee TODO antes de ejecutar.
--
-- ANTES DE NADA:
--   0) Toma un SNAPSHOT/BACKUP de la BD en Railway (Database → Backups).
--   1) Corre la FASE 1 (read-only). Revisa los grupos y los sobrevivientes.
--   2) Corre la FASE 2 (transacción). Revisa los CONTEOS de control.
--      La transacción termina en ROLLBACK por default: NO cambia nada hasta
--      que cambies la última línea a COMMIT.
--   3) Tras el COMMIT, corre la FASE 3: reconcilia el saldo de cada
--      sobreviviente con el endpoint de la app (NO en SQL, ver abajo).
--
-- REGLA DE SOBREVIVIENTE: por RFC, gana la empresa con MÁS órdenes de venta;
-- empate → el id más bajo (registro más antiguo). La FASE 1 te muestra el
-- sobreviviente propuesto por grupo. Si para algún grupo quieres OTRO
-- sobreviviente, dímelo y te paso una variante del script.
--
-- Re-mapea estas 4 FKs hacia el sobreviviente antes de borrar:
--   ordenes_venta.cliente_id, transacciones_clientes.cliente_id,
--   remisiones.cliente_id, contactos.cliente_id
-- ============================================================================


-- ╔══════════════════════════════════════════════════════════════════════╗
-- ║ FASE 1 — PREVIEW (read-only, NO cambia nada). Corre y revisa.          ║
-- ╚══════════════════════════════════════════════════════════════════════╝
WITH grupos AS (
  SELECT rfc_tax_id
  FROM clientes
  WHERE rfc_tax_id IS NOT NULL AND btrim(rfc_tax_id) <> ''
  GROUP BY rfc_tax_id
  HAVING count(*) > 1
),
conteo AS (
  SELECT c.id, c.rfc_tax_id, c.nombre_empresa, c.contacto_nombre,
         c.saldo_actual, c.limite_credito,
         (SELECT count(*) FROM ordenes_venta o         WHERE o.cliente_id  = c.id) AS n_ordenes,
         (SELECT count(*) FROM transacciones_clientes t WHERE t.cliente_id = c.id) AS n_transacciones,
         (SELECT count(*) FROM remisiones r            WHERE r.cliente_id  = c.id) AS n_remisiones,
         (SELECT count(*) FROM contactos co            WHERE co.cliente_id = c.id) AS n_contactos
  FROM clientes c
  JOIN grupos g ON g.rfc_tax_id = c.rfc_tax_id
),
ranked AS (
  SELECT *,
         row_number() OVER (PARTITION BY rfc_tax_id ORDER BY n_ordenes DESC, id ASC) AS rn
  FROM conteo
)
SELECT rfc_tax_id,
       CASE WHEN rn = 1 THEN '★ SOBREVIVE' ELSE '  se fusiona →' END AS rol,
       id, nombre_empresa, contacto_nombre,
       n_ordenes, n_transacciones, n_remisiones, n_contactos,
       saldo_actual, limite_credito
FROM ranked
ORDER BY rfc_tax_id, rn;


-- ╔══════════════════════════════════════════════════════════════════════╗
-- ║ FASE 2 — MERGE (TRANSACCIÓN). Corre TODO este bloque junto.            ║
-- ║ Revisa los conteos; cambia ROLLBACK → COMMIT solo si cuadra.          ║
-- ╚══════════════════════════════════════════════════════════════════════╝
BEGIN;

CREATE TEMP TABLE _merge_map ON COMMIT DROP AS
WITH grupos AS (
  SELECT rfc_tax_id
  FROM clientes
  WHERE rfc_tax_id IS NOT NULL AND btrim(rfc_tax_id) <> ''
  GROUP BY rfc_tax_id
  HAVING count(*) > 1
),
ranked AS (
  SELECT c.id, c.rfc_tax_id,
         row_number() OVER (
           PARTITION BY c.rfc_tax_id
           ORDER BY (SELECT count(*) FROM ordenes_venta o WHERE o.cliente_id = c.id) DESC, c.id ASC
         ) AS rn
  FROM clientes c
  JOIN grupos g ON g.rfc_tax_id = c.rfc_tax_id
)
SELECT l.id AS loser_id, s.id AS survivor_id, l.rfc_tax_id
FROM ranked l
JOIN ranked s ON s.rfc_tax_id = l.rfc_tax_id AND s.rn = 1
WHERE l.rn > 1;

-- Salvaguarda: aborta si algún sobreviviente aparece también como perdedor.
DO $$
DECLARE bad int;
BEGIN
  SELECT count(*) INTO bad FROM _merge_map WHERE survivor_id IN (SELECT loser_id FROM _merge_map);
  IF bad > 0 THEN RAISE EXCEPTION 'merge_map inconsistente: % survivor también es loser', bad; END IF;
END $$;

-- Re-mapear las 4 FKs hacia el sobreviviente
UPDATE ordenes_venta          o  SET cliente_id = m.survivor_id FROM _merge_map m WHERE o.cliente_id  = m.loser_id;
UPDATE transacciones_clientes t  SET cliente_id = m.survivor_id FROM _merge_map m WHERE t.cliente_id  = m.loser_id;
UPDATE remisiones             r  SET cliente_id = m.survivor_id FROM _merge_map m WHERE r.cliente_id  = m.loser_id;
UPDATE contactos              co SET cliente_id = m.survivor_id FROM _merge_map m WHERE co.cliente_id = m.loser_id;

-- Borrar las empresas perdedoras (ya sin hijos)
DELETE FROM clientes c USING _merge_map m WHERE c.id = m.loser_id;

-- ── CONTEOS DE CONTROL (revísalos antes de COMMIT) ──
SELECT count(*) AS empresas_fusionadas FROM _merge_map;
SELECT count(DISTINCT survivor_id) AS sobrevivientes FROM _merge_map;
SELECT count(*) AS empresas_totales_despues FROM clientes;

-- >>> Si los conteos cuadran, cambia la siguiente línea a:  COMMIT;
ROLLBACK;
-- COMMIT;


-- ╔══════════════════════════════════════════════════════════════════════╗
-- ║ FASE 3 — RECONCILIAR SALDO (NO en SQL; usar la app, lógica probada)   ║
-- ╚══════════════════════════════════════════════════════════════════════╝
-- Tras el COMMIT, el saldo_actual de cada SOBREVIVIENTE quedó desactualizado
-- (ahora tiene las transacciones de los perdedores, pero el caché no se movió).
-- Reconcílialo con el endpoint admin ya probado, POR CADA sobreviviente (★):
--
--   POST /api/clientes/{survivor_id}/saldo-reconciliacion/aplicar
--
-- (Los ids ★ los ves en la FASE 1.) Ese endpoint recalcula saldo_actual desde
-- transacciones con la lógica de la app (tolera enums legacy CARGO/ABONO),
-- por eso NO recomputamos el saldo en SQL crudo.
--
-- NOTA: el sobreviviente puede quedar con varios contactos es_principal=true
-- (uno por empresa fusionada). Limpia el principal en el detalle de la empresa
-- si hace falta (el endpoint de contactos re-sincroniza el trío denormalizado).
