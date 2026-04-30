# Troubleshooting

## 500 al crear usuario / dashboard / historial

**Causa**: alguna columna nueva no existe en la DB. En Railway no corre `alembic upgrade head`, así que las columnas agregadas en migraciones recientes deben listarse en `app/db/seeds.py::_BACKFILL_DDL` para que `lifespan` las cree con `ALTER TABLE IF NOT EXISTS …`.

**Fix**:

1. Verificar el log de startup de Railway (Logs en el servicio). Buscar el `Backfill DDL skip` o el traceback.
2. Si es columna que vos agregaste, sumá la sentencia equivalente al final de `_BACKFILL_DDL` en `app/db/seeds.py`. Push. Railway redeploya y la columna queda.
3. Si la columna ya existe (caso común local cuando `create_all` la creó antes que alembic): correr `alembic stamp head`.

## Mixed content en producción Railway

`(index):64 Mixed Content: ... requested an insecure stylesheet 'http://...'`

**Causa**: `url_for('static', …)` no detecta el `X-Forwarded-Proto: https` del proxy de Railway.

**Fix ya aplicado**: `ProxyHeadersMiddleware(trusted_hosts="*")` en `app/main.py`. Si el problema reaparece en algún template específico, usar path absoluto `/static/css/...` en lugar de `url_for`.

## Tipo de cambio USD/MXN no carga

```
GET /api/fx/usd-mxn → 502 No se pudo obtener TC de ninguna fuente
```

**Diagnóstico**:

1. Verifica `BANXICO_TOKEN` en env. Sin él, la app cae al fallback `open.er-api.com`.
2. Probá manualmente: `curl https://open.er-api.com/v6/latest/USD`. Si esta API también falla, hay corte de internet.
3. Si Banxico funciona, suele devolver 401 cuando el token es inválido. Renová en https://www.banxico.org.mx/SieAPIRest/service/v1/token/registro.

**Cache**: hay 1 row por día en `tipos_cambio_dia`. Si el TC del día está cacheado y querés refrescarlo, `POST /api/fx/refresh` (admin).

## Seed de context/ no carga datos

**Síntomas**: tabla `productos` vacía después del primer arranque.

**Diagnóstico**:

```bash
# revisar logs
grep "Seed context/" /tmp/dasic-uvicorn.log     # local
# en Railway: Logs > buscar "Seed context/"
```

Si no aparece la línea: `SEED_CONTEXT_DISABLED=1` está seteada. Quitala y reinicia.

Si aparece "Seed context/ FALLÓ": traceback indica el problema (archivo Excel ausente, FK rota, etc.). Disparalo manual desde DevTools logueado como admin:

```javascript
fetch('/api/admin/seed-context', {method:'POST', credentials:'include'})
  .then(r => r.json()).then(console.log)
```

## Tailwind CDN warning

```
cdn.tailwindcss.com should not be used in production. To use Tailwind CSS in production, install it as a PostCSS plugin or use the Tailwind CLI...
```

**Sólo es un warning del Play CDN**. No bloquea nada. Para silenciarlo hay que migrar a build PostCSS — se intentó (commit `e622245`) y se revirtió porque rompió `@apply` en `dax-*`. Pendiente para un sprint con foco frontend.

## Login con email mayúsculas no entra

Los emails se guardan con el caso que envió el usuario. La validación es por igualdad estricta. Verificá que coincide caso-sensitivo. (Mejora pendiente: normalizar a minúsculas al guardar y al buscar.)

## "Stock insuficiente" al convertir cotización a venta

Otra cotización tiene reserva activa sobre el mismo producto. Para resolver:

1. Identificar las cotizaciones con reservas activas:
   ```sql
   SELECT ov.id, ov.folio, ov.estatus, do.cantidad, p.sku
   FROM ordenes_venta ov
   JOIN detalles_orden do ON do.orden_id = ov.id
   JOIN productos p ON p.id = do.producto_id
   WHERE ov.estatus = 'COTIZACION' AND p.id = <ID_PRODUCTO>;
   ```
2. Cancelar las que no se vayan a convertir, o esperar a que venzan (`POST /api/inventario/liberar-vencidas`).

## Endpoint devuelve `{"detail":"No tienes permiso para …"}`

RBAC funcionando. El rol del user no permite la acción. Ver:

- Matriz declarativa: `app/security/permissions.py::PERMISSIONS`.
- Lo que el frontend cree que puede hacer: `GET /api/auth/me`.
- Documento de roles: `docs/onboarding/70_rbac_y_roles.md`.

Si un rol *debería* poder hacer la acción, agregar la tupla `(action, resource)` al set del rol y rebootear (lifespan no necesita migración para esto).

## Admin elimina al usuario que está logueado

Devuelve 400 "No puedes eliminarte a ti mismo". Es por diseño. Si necesitás bajar al admin desde otro admin, primero crear un segundo admin, hacer login con ése, y borrar al primero.

## `cdn.min.js` (Alpine) no inicializa el sidebar

Limpia caché del browser (Ctrl+Shift+R). El bundle viene de CDN y tiende a cachearse agresivamente. Si persiste, abrir DevTools → Application → Storage → Clear site data.
