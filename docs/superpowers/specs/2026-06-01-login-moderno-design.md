# Login moderno (split-screen) — Design

**Fecha:** 2026-06-01
**Alcance:** Rediseño visual de `web/src/features/auth/pages/LoginPage.tsx` a un layout split-screen moderno. **Solo presentación** — la lógica (redirect por `/me`, `onSubmit` form-urlencoded con `remember`, estados, manejo de error) se conserva idéntica.

## Estado actual

Tarjeta oscura única centrada (max-w-md) sobre degradado `slate-950→900`: logo, "Atlas ONE", correo, contraseña con ojo, checkbox "Recordar sesión", botón `accent-glow`, pie "Powered by Atlas Tech". Limpio pero genérico; desperdicia el ancho en desktop.

## Decisión

**Split-screen de marca** (patrón enterprise). Aprobado por el usuario.

## Diseño

- **Contenedor:** `min-h-screen flex`. En desktop dos paneles 50/50; en móvil el panel de marca se oculta y el formulario ocupa todo con el logo arriba.
- **Panel izquierdo (marca)** `hidden lg:flex lg:w-1/2`:
  - Degradado industrial (slate oscuro + glow del acento) con 1-2 "blobs" radiales sutiles de `accent-glow` a baja opacidad.
  - Logo (`/static/img/Logo_main.png`, con fallback `display:none`), "Atlas ONE", tagline "Sistema Industrial · DASIC".
  - 3 bullets de valor con ícono check: "Cotizaciones en minutos", "Inventario y reservas en vivo", "OC, remisiones y reportes".
  - Pie discreto "Powered by Atlas Tech · Atlas ONE v2.0".
- **Panel derecho (formulario)** `flex-1 flex items-center justify-center`:
  - Logo compacto arriba **solo visible en móvil** (`lg:hidden`).
  - Encabezado "Bienvenido de vuelta" + subtítulo "Inicia sesión en Atlas ONE".
  - Bloque de error (igual que hoy), Correo, Contraseña con ojo, checkbox Recordar, botón submit con estado busy.
  - Inputs y botón conservan el estilo `accent-glow` (foco con ring/borde glow).
- **Responsive:** `lg:` breakpoint divide los paneles; abajo de `lg` solo el formulario centrado (max-w-sm) con el logo móvil.
- **Accesibilidad:** labels, `autoFocus` en correo, `autoComplete`, `aria-label` del toggle de contraseña — todo se mantiene.

## Fuera de alcance

- Cambios de lógica/auth (handlers idénticos).
- Tema claro para el login (sigue dark, como hoy).
- Ilustraciones/imágenes nuevas (solo CSS + el logo existente).

## Verificación

- `cd web && npm run build` → `✓ built` sin errores TS.
- Manual: el login se ve split en desktop ≥1024px y de una columna en móvil; login funciona igual (correo/contraseña, recordar, error, redirect a dashboard).
