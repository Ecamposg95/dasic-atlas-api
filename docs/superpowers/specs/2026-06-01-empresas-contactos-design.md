# Sub-proyecto 1 — Empresa + Contactos (base) — Design

**Fecha:** 2026-06-01
**Contexto:** El dominio de clientes mezcla empresa + persona + crédito en una sola tabla `clientes`. El usuario quiere: una empresa con varias personas (contactos), crédito por empresa, CRUD más completo y un "área de empresas". Decomposición acordada en 3 sub-proyectos; este es el **1 (base)**. Sub-2 (contacto en la cotización) y sub-3 (dedup de duplicados, destructivo) van después.

## Decisiones de producto (acordadas)

1. **Modelo:** la tabla `clientes` REPRESENTA la **empresa** (conserva crédito/saldo y todas las FKs de `OrdenVenta.cliente_id`/`TransaccionCliente.cliente_id` — cero migración destructiva). Se agrega tabla `contactos` (personas) que cuelga de la empresa.
2. **No tocar la cotización** en este sub-proyecto (eso es sub-2).
3. **No deduplicar** empresas existentes (eso es sub-3).

## Arquitectura

### 1. Modelo `Contacto` (migración aditiva + backfill)

`app/models/clients.py` — nuevo modelo `Contacto`:
- `id` PK
- `cliente_id` Integer FK → `clientes.id` (ON DELETE CASCADE; index)
- `nombre` String(120) NOT NULL
- `cargo` String(80) nullable (puesto: Compras, Almacén, etc.)
- `email` String(120) nullable
- `telefono` String(40) nullable
- `es_principal` Boolean NOT NULL default false
- `creado_en` DateTime(timezone=True) server_default now()
- relationship `cliente` (back_populates `contactos`); en `Cliente` agregar `contactos = relationship("Contacto", back_populates="cliente", cascade="all, delete-orphan")`.

`clientes` (empresa) **no cambia**: conserva `nombre_empresa`, `rfc_tax_id`, `direccion`, crédito (`limite_credito`, `dias_credito`, `dia_corte`, `moneda_credito`, `saldo_actual`), y `contacto_nombre/email/telefono` como **contacto principal denormalizado** (lo que ya leen el ClientPicker y los PDFs → no se rompen). Ese trío se mantiene sincronizado desde el contacto marcado `es_principal`.

**Migración** `migrations/versions/20260601_05_contactos.py`: `CREATE TABLE contactos (...)` con FK ON DELETE CASCADE + index en `cliente_id`. Espejo en `_BACKFILL_DDL` (`CREATE TABLE IF NOT EXISTS contactos ...` + index) porque Railway no corre alembic.

**Backfill de datos (idempotente):** `seed_contactos_principal(db)` en `run_all_seeds`: por cada `Cliente` con `contacto_nombre` no vacío que aún no tenga ningún contacto, crear un `Contacto(es_principal=True)` copiando nombre/email/telefono. No-op tras la primera corrida.

### 2. Backend — endpoints de contactos

En `app/routers/clientes.py`:
- `GET /api/clientes/{cliente_id}/contactos` → lista de contactos de la empresa.
- `POST /api/clientes/{cliente_id}/contactos` → crea contacto. Si `es_principal=True`: desmarca el principal anterior y **sincroniza** `cliente.contacto_nombre/email/telefono` desde el nuevo.
- `PATCH /api/clientes/{cliente_id}/contactos/{contacto_id}` → actualiza; mismo manejo de `es_principal` + sync. (Anidado bajo `/api/clientes` para validar ownership y no requerir router nuevo.)
- `DELETE /api/clientes/{cliente_id}/contactos/{contacto_id}` → elimina (si era principal, no re-sincroniza el trío del empresa — queda el último valor; opcional limpiar).
- **`n_contactos` en el listado queda fuera del sub-1** (no se toca `GET /api/clientes/`); el conteo de contactos se ve en el detalle. Se puede agregar después si se quiere la columna.

Schemas en `app/schemas/clients.py`: `ContactoBase`, `ContactoCreate`, `ContactoUpdate`, `ContactoResponse`. **Re-exportar en `app/schemas/__init__.py`** (import + `__all__`) — gotcha conocido [[feedback-schemas-reexport]].

### 3. Backend — agregados del detalle de empresa

No requiere endpoints nuevos: el detalle reutiliza los **existentes** (hoy sin consumidor SPA): `GET /api/clientes/{id}/estado-cuenta`, `GET /api/clientes/{id}/cuentas-por-cobrar`, `POST /api/clientes/{id}/registrar-pago`.

### 4. Frontend — área de empresas (`web/src/features/clientes/`)

- **`ClientesPage`** se presenta como **"Empresas"**: encabezado/labels actualizados; tabla con Empresa · RFC · Contacto principal · Crédito · Saldo · Acciones (# contactos se ve en el detalle, no en la lista — ver arriba). Mantiene crear/editar empresa (form actual) y eliminar.
- **`EmpresaDetalleDrawer`** (nuevo): panel lateral/modal grande que abre al "Ver" una empresa, con 3 secciones:
  1. **Datos & crédito** — datos de la empresa (reusa/enlaza el `ClienteFormModal` para editar).
  2. **Contactos** — lista de contactos con agregar/editar/eliminar y marcar principal (CRUD contra los endpoints nuevos).
  3. **Estado de cuenta / CxC** — transacciones (estado-cuenta), cargos abiertos (cuentas-por-cobrar) y **registrar pago** (cableando los endpoints existentes).
- **Tipos y hooks:** `types.ts` += `Contacto`; nuevos hooks `useContactos(clienteId)`, `useCrearContacto`/`useActualizarContacto`/`useEliminarContacto`, y `useEstadoCuenta(clienteId)`, `useCxCCliente(clienteId)`, `useRegistrarPago`.

### 5. Cobertura

| Requisito del usuario | Cómo se cubre |
|------------------------|---------------|
| Misma empresa, varias personas | Tabla `contactos` + CRUD en el detalle. |
| Crédito por empresa | Ya está en `clientes` (la empresa); se preserva. |
| CRUD más completo | Detalle de empresa con datos+crédito, contactos y estado de cuenta/CxC. |
| Área más específica para empresas | `EmpresaDetalleDrawer` + página presentada como Empresas. |

## Fuera de alcance (este sub-proyecto)

- Contacto en la cotización / `OrdenVenta.contacto_id` / picker empresa→contacto / "Atención" en PDF (sub-2).
- Dedup/merge de empresas duplicadas (sub-3, destructivo y auditado).
- Renombrar la tabla `clientes` o sus rutas (`/api/clientes`, `/spa/clientes` se conservan; solo cambia la presentación).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`.
- **Migración aditiva** (nueva tabla + FK CASCADE) → bajo riesgo; espejo en `_BACKFILL_DDL`; backfill idempotente en seeds.
- **Re-export de schemas** nuevos (`Contacto*`) en `__init__.py` [[feedback-schemas-reexport]].
- **No-breaking:** el ClientPicker y los PDFs siguen leyendo `cliente.contacto_nombre/email`; el contacto principal los mantiene sincronizados.
