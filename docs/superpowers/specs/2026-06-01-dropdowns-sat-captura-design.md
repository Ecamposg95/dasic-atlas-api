# Dropdowns SAT en campos de captura — Design

**Fecha:** 2026-06-01
**Alcance:** Reemplazar los inputs de texto libre de los campos SAT de captura (`clave_prod_serv`, `clave_unidad_sat`) por un combobox con búsqueda (typeahead) en producto, fantasma (editar) y cotizador (agregar fantasma). Sembrar un set curado de claves de unidad para que el dropdown tenga datos.

## Contexto actual (auditado)

- **Modelos y endpoints typeahead YA existen** (`app/models/sat.py`, `app/routers/sat.py`):
  - `GET /api/sat/clave-prod-serv?q=&limit=20` (q ≥ 2 chars) → `[{codigo, descripcion, palabras_clave, ...}]`. Tabla `sat_clave_prodserv` (PK VARCHAR(8)) **VACÍA** (sin importer).
  - `GET /api/sat/clave-unidad?q=&limit=20` (q ≥ 1 char) → `[{codigo, nombre, descripcion, simbolo, activo}]`. Tabla `sat_clave_unidad` (PK VARCHAR(3)) **VACÍA**.
  - Ambos requieren `allow_all_staff`.
- **Campos de captura (3 lugares, inputs de texto libre):**
  - `web/src/features/inventario/components/ProductoFormModal.tsx` (~180-190): `claveProdServ` / `claveUnidadSat`.
  - `web/src/features/fantasmas/pages/FantasmasPage.tsx` (~562-569, modal editar): `claveProdServ` / `claveUnidadSat`.
  - `web/src/features/cotizador/components/AgregarFantasmaModal.tsx` (~362-367): `claveProdServ` / `claveUnidadSat`.
  - (Servicios usa defaults SAT en DB, sin captura — fuera de alcance.)
- **No existe combobox/autocomplete reutilizable**; `components/ui/select.tsx` es `<select>` plano. Sí existe el patrón de dropdown con búsqueda debounced en `web/src/features/cotizador/components/ClientPicker.tsx` (referencia a reusar).
- Seeds: `app/db/seeds.py` siembra los 10 catálogos chicos vía `seed_sat_catalogos_pequenos()` leyendo `app/data/sat/*.py`. ClaveUnidad/ClaveProdServ no se siembran hoy.

## Decisiones de producto (acordadas)

1. **ClaveUnidad:** sembrar un set CURADO (~35 claves comunes) → dropdown con datos inmediatos.
2. **ClaveProdServ:** NO sembrar el catálogo completo (52k, requiere archivo oficial). El combobox busca lo que haya y permite **texto libre** como fallback.
3. El `value` del campo sigue siendo el **código string** → retrocompatible con lo que ya se persiste.

## Arquitectura

### 1. Backend — seeder de ClaveUnidad curada

- `app/data/sat/clave_unidad_comunes.py`: lista `CLAVE_UNIDAD_COMUNES = [(codigo, nombre), ...]` con ~35 claves SAT comunes (H87 Pieza, E48 Unidad de servicio, KGM Kilogramo, GRM Gramo, MTR Metro, CMT Centímetro, MMT Milímetro, MTK Metro cuadrado, MTQ Metro cúbico, LTR Litro, MLT Mililitro, XBX Caja, XPK Paquete, XRO Rollo, XBE Manojo, SET Conjunto, KT Kit, HUR Hora, DAY Día, MON Mes, ANN Año, PR Par, DZN Docena, C62 Uno/Unidad, XUN Unidad, A9 Tarifa, E51 Trabajo, ACT Actividad, etc.).
- `seed_sat_clave_unidad(db)` en `seeds.py`: idempotente — por cada `(codigo, nombre)`, inserta `SatClaveUnidad` si no existe ese `codigo` (`activo=True`). Enganchado en `run_all_seeds()` junto a los demás seeds SAT. La tabla la crea `create_all` desde el modelo `SatClaveUnidad`.
- Sin migración (la tabla ya existe en el modelo; create_all/lifespan la materializa).

### 2. Frontend — componente `SatCombobox`

`web/src/components/ui/sat-combobox.tsx` (nuevo, reutilizable):
- Props: `value: string`, `onChange: (code: string) => void`, `endpoint: string` (`/api/sat/clave-unidad` | `/api/sat/clave-prod-serv`), `minChars?: number` (default 2), `placeholder?`, `maxLength?`, `className?`.
- Comportamiento (patrón `ClientPicker`):
  - Un `Input` editable cuyo texto **es** el `value` (código). Escribir llama `onChange` directo → texto libre siempre permitido (fallback).
  - Con `query.length >= minChars`, hace `GET {endpoint}?q={query}&limit=20` (debounce ~250ms, `credentials:'include'`) y muestra un panel con resultados `{codigo} — {descripcion ?? nombre}`.
  - Click en un resultado → `onChange(codigo)` y cierra el panel.
  - Maneja ambas formas de respuesta leyendo `item.descripcion ?? item.nombre ?? ''` para la etiqueta.
  - Sin dependencias nuevas (fetch directo + estado local, igual que ClientPicker). 401 → no rompe (panel vacío).
- Tipo de respuesta: `type SatItem = { codigo: string; descripcion?: string | null; nombre?: string | null }`.

### 3. Cablear en los 3 lugares de captura

En cada modal, reemplazar los dos `<Input>` SAT por `<SatCombobox>`:
- `clave_prod_serv` → `<SatCombobox endpoint="/api/sat/clave-prod-serv" minChars={2} maxLength={8} value={claveProdServ} onChange={setClaveProdServ} placeholder="Buscar o escribir (ej. 31181701)" />`
- `clave_unidad_sat` → `<SatCombobox endpoint="/api/sat/clave-unidad" minChars={1} maxLength={10} value={claveUnidadSat} onChange={setClaveUnidadSat} placeholder="Buscar unidad (ej. H87)" />`

Las variables de estado (`claveProdServ`/`claveUnidadSat`) y el payload no cambian — siguen siendo strings. Solo cambia el control de captura.

### 4. Cobertura

| Requisito | Cómo se cubre |
|-----------|---------------|
| Dropdown SAT en captura | `SatCombobox` en los 3 modales. |
| Unidad SAT con datos | Seeder curado de ~35 claves. |
| Clave prod/serv buscable | Combobox typeahead (busca lo sembrado) + texto libre. |
| Retrocompatibilidad | `value` sigue siendo el código string. |

## Fuera de alcance (YAGNI)

- Importar el catálogo completo de ClaveProdServ (52k) — requiere archivo oficial del SAT; tarea de datos separada.
- Captura SAT en Servicios (usa defaults en DB).
- Los 10 catálogos chicos de factura (forma de pago, uso CFDI, etc.) — son para CFDI, no para captura de producto.
- Validar que el código exista en el catálogo (se permite texto libre a propósito).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`.
- **Datos:** el seeder es idempotente y la tabla la crea create_all → bajo riesgo. En Railway corre en lifespan (`run_all_seeds`).
- **Degradación limpia:** mientras ClaveProdServ esté vacía, el combobox no devuelve resultados pero el texto libre sigue funcionando → nadie queda bloqueado.
- **Sin migración** ni cambios de payload/contrato.
