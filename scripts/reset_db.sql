-- ============================================================================
-- RESET TOTAL DE LA BASE DE DATOS — opción nuclear
-- ============================================================================
--
-- BORRA TODO el schema `public`: tablas, secuencias, datos, índices, todo.
-- Tras ejecutar esto, al reiniciar la app (Railway redeploy) el lifespan
-- (app/main.py → app/core/lifespan.py) volverá a:
--   1. Crear todas las tablas vía Base.metadata.create_all()
--   2. Aplicar _BACKFILL_DDL (idempotente)
--   3. Sembrar la organización "DASIC Industrial" + branch HQ
--   4. Crear admin@dasic.com / admin123 (porque no habrá usuarios)
--
-- ⚠️ IRREVERSIBLE. Sin backup previo. Solo ejecutar cuando estés seguro de
--    que los datos actuales no importan.
--
-- USO:
--   railway run psql $DATABASE_URL -f scripts/reset_db.sql
--
--   o desde el panel de Railway → tu servicio Postgres → "Query":
--     pegar el contenido y ejecutar.
--
--   o cualquier cliente psql apuntando a Railway:
--     psql "$DATABASE_URL" -f scripts/reset_db.sql
--
-- TRAS EJECUTAR:
--   1. Railway redeploy (push a main, o `railway up`, o reinicio manual)
--   2. Esperar ~30s a que el lifespan corra
--   3. Login con admin@dasic.com / admin123 y cambiar contraseña
-- ============================================================================

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- Permisos estándar de Postgres para el schema recién creado.
-- Railway crea la DB con un usuario único (no necesariamente "postgres"),
-- así que aplicamos GRANT a CURRENT_USER y a PUBLIC para máxima compat.
GRANT ALL ON SCHEMA public TO CURRENT_USER;
GRANT ALL ON SCHEMA public TO PUBLIC;

-- Verificación: lista de tablas debe estar vacía después de esto.
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public';
