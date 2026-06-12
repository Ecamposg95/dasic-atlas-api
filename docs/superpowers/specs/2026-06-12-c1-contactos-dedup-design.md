# C1 — Unificar contactos (form + hooks compartidos)

**Fecha:** 2026-06-12
**Estado:** Aprobado para plan
**Alcance:** Workstream C, sub-proyecto 1 (de-duplicación de Contactos). C2–C6 van en specs aparte.

## Contexto

Auditoría de los 24 módulos: el dominio Contactos tiene UI/lógica duplicada en el frontend. Tras inspeccionar el código (2026-06-12) la duplicación real es **más chica** de lo que sugería la auditoría:

- **Backend NO duplicado.** `app/routers/contactos.py` es **solo lectura** (lista global cross-empresa con q/sort/dir/paginación en `GET /api/contactos/` + `GET /api/contactos/{id}/historial`). Todo el write vive en UN solo lugar: `GET/POST/PATCH/DELETE /api/clientes/{cliente_id}/contactos[/{id}]` en `app/routers/clientes.py`.
- **Frontend SÍ duplicado:**
  1. **Dos formularios:** `features/contactos/components/ContactoFormModal.tsx` (modal, usado por el directorio global) y un form **inline** dentro de `features/clientes/components/tabs/ContactosTab.tsx`. Ambos arman el mismo payload y llaman a `useGuardarContacto`.
  2. **Dos tipos:** `ContactoGlobal` (`features/contactos/types.ts`) vs `Contacto` + `ContactoInput` (`features/clientes/types.ts`).
  3. **Hooks de contacto mal ubicados:** `useContactos(clienteId)`, `useGuardarContacto(clienteId)`, `useEliminarContacto(clienteId)` viven en `features/clientes/hooks/useEmpresaDetalle.ts` (mezclados con lógica de empresa), aunque son del dominio Contactos. El modal global ya los importa desde ahí (los hooks de escritura ya están de facto compartidos).

**Decisión del usuario:** unificar form + hooks compartidos, **manteniendo edición en ambas superficies** (directorio global y tab de empresa). No colapsar ninguna vista.

## Objetivos

- Un solo formulario de contacto (`ContactoFormModal`) usado por el directorio global y por el tab de la empresa.
- Un solo tipo canónico de contacto.
- Los hooks de contacto pertenecen al dominio Contactos (`features/contactos/hooks/`), no a `useEmpresaDetalle`.
- Cero cambios de comportamiento observable salvo que el tab pase de form inline a modal. Cero cambios de backend/esquema.

## No-objetivos

- NO tocar backend ni esquema (los endpoints de write siguen bajo `/api/clientes/{id}/contactos`).
- NO colapsar el directorio global ni el tab (ambas vistas se conservan).
- NO tocar otros sub-proyectos de C (Usuarios, Borradores, Servicios, Precios, Remisiones≈Actas).

## Diseño

### Unidad 1 — Tipo canónico (`features/contactos/types.ts`)
Definir el tipo editable canónico y derivar el global de él:
```ts
export type Contacto = {
  id: number;
  cliente_id: number;
  nombre: string;
  cargo: string | null;
  email: string | null;
  telefono: string | null;
  es_principal: boolean;
};
export type ContactoInput = {
  nombre: string;
  cargo: string | null;
  email: string | null;
  telefono: string | null;
  es_principal: boolean;
};
export type ContactoGlobal = Contacto & { empresa_nombre: string | null };
```
`features/clientes/types.ts` deja de declarar `Contacto`/`ContactoInput` y los **re-exporta** desde `@/features/contactos/types` (para no romper importadores). Verificar y ajustar los importadores reales (tab, EmpresaDetalle, ClientPicker del cotizador, useEmpresaDetalle).

### Unidad 2 — Hooks de contacto (`features/contactos/hooks/useContactoMutations.ts`, nuevo)
Mover desde `features/clientes/hooks/useEmpresaDetalle.ts`:
- `useContactosEmpresa(clienteId: number | null)` — `GET /api/clientes/{id}/contactos` (hoy `useContactos`; se renombra para que el dominio sea explícito y no choque con el `useContactosGlobal`).
- `useGuardarContacto(clienteId: number)` — POST (sin id) / PATCH (con id) a `/api/clientes/{id}/contactos`.
- `useEliminarContacto(clienteId: number)` — DELETE.
Conservar EXACTO el patrón de invalidación actual: invalidar `['contactos', clienteId]` y `['contactos', 'global']` (y lo que ya invalide hoy, p.ej. resumen de empresa). `useEmpresaDetalle.ts` deja de exportar estas 3 funciones; sus importadores pasan a importar desde `features/contactos/hooks/useContactoMutations`. El resto de `useEmpresaDetalle` (resumen, actividad, notas, deals, cxc) queda intacto.

### Unidad 3 — `ContactoFormModal` como único formulario
Agregar prop opcional `clienteIdFijo?: number`:
- Cuando viene (abierto desde el tab de empresa): NO renderizar el selector de empresa; `empresaId = clienteIdFijo` fijo; guarda contra esa empresa.
- Cuando no viene (global "Nuevo" / editar global): comportamiento actual (selector de empresa visible, precargado de `editing?.cliente_id`).
El modal importa `useGuardarContacto` desde `features/contactos/hooks/useContactoMutations` (no desde clientes). Acepta `editing: ContactoGlobal | Contacto | null` (la forma base alcanza; `empresa_nombre` no se usa en el form).

### Unidad 4 — Refactor `ContactosTab`
- Conservar: tabla de contactos, botón "Nuevo", acciones editar/eliminar, toggle ★ principal, estado vacío.
- Quitar: el form inline (`VACIO`, `form`/`setForm`, `showForm`, el bloque de `<Input>` inline, `guardarContacto`).
- "Nuevo" → abre `<ContactoFormModal clienteIdFijo={clienteId} editing={null} />`. "Editar" → `<ContactoFormModal clienteIdFijo={clienteId} editing={contacto} />`.
- Importar `useContactosEmpresa`/`useEliminarContacto` desde `features/contactos/hooks/useContactoMutations`. El toggle ★ principal sigue usando `useGuardarContacto` (PATCH con `es_principal`).

### Unidad 5 — Limpieza
Borrar el código muerto: form inline del tab, declaraciones `Contacto`/`ContactoInput` duplicadas en `clientes/types.ts` (reemplazadas por re-export), y las 3 funciones de contacto removidas de `useEmpresaDetalle.ts`.

## Data flow
- Directorio global: `useContactosGlobal` (read `/api/contactos/`) + `<ContactoFormModal>` (sin `clienteIdFijo`) → write `/api/clientes/{id}/contactos`.
- Tab de empresa: `useContactosEmpresa(clienteId)` (read `/api/clientes/{id}/contactos`) + `<ContactoFormModal clienteIdFijo={clienteId}>` → mismo write.
- Ambos comparten tipo, hooks de escritura y formulario. La cross-invalidación ya mantiene los dos caches sincronizados.

## Riesgos
- **Reconciliar tipos** (`Contacto` vs `ContactoGlobal` vs `ContactoInput`) sin romper compilación en consumidores: tab, `EmpresaDetallePage`, `ClientPicker` del cotizador, `useEmpresaDetalle`. Es lo más delicado; mitigar con `npm run build` (tsc) tras cada unidad.
- El modo `clienteIdFijo` debe ocultar el selector y no exigir empresa al guardar.

## Validación
- Sin backend → solo `cd web && npm run build` verde (tsc + vite). `app/static/dist/` se commitea.
- QA visual del usuario: en el directorio global y en el tab de empresa — crear/editar/eliminar contacto, toggle ★ principal, "Nuevo" global pide empresa, "Nuevo" en tab la bloquea. Light/dark.

## Secuencia de implementación
1. Tipo canónico + re-export (Unidad 1) → build.
2. Mover hooks a `useContactoMutations` + re-apuntar importadores (Unidad 2) → build.
3. `clienteIdFijo` en el modal (Unidad 3) → build.
4. Refactor `ContactosTab` al modal (Unidad 4) + limpieza (Unidad 5) → build.
