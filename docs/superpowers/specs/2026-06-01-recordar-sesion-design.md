# US-031 — Política de sesión ("Recordar sesión") — Design

**Fecha:** 2026-06-01
**Alcance:** US-031 (control explícito de persistencia de sesión vía un checkbox "Recordar sesión" en el login).

## Contexto actual (auditado)

- `POST /api/auth/login` (auth.py) usa `OAuth2PasswordRequestForm` (form-urlencoded: `username`/`password`). Crea el JWT con `expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)` (default **720 min = 12h**) y setea la cookie `access_token = "Bearer <jwt>"` con `httponly=True`, `samesite="lax"`, `secure=cookie_secure`, y **`max_age = ACCESS_TOKEN_EXPIRE_MINUTES*60`** → cookie **persistente** de 12h.
- Efecto actual: **todos quedan "recordados" 12h** sin elegirlo (la cookie persistente sobrevive al cierre del navegador). No hay checkbox, refresh tokens, ni aviso de expiración.
- `GET /api/auth/me` revalida `current_user.activo` en cada carga (un admin que desactiva al usuario lo bloquea aunque el JWT siga vivo). El frontend (`Layout`) rehidrata desde `/me`.
- `POST /api/auth/logout` borra la cookie server-side (`delete_cookie`).
- Frontend `LoginPage.tsx` hace `fetch('/api/auth/login', { headers: {'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams({ username: email, password }) })`.

## Decisiones de producto (acordadas)

1. **Modelo:** cookie **persistente vs de sesión**. Sin marcar → cookie de sesión (se borra al cerrar el navegador) + JWT 12h. Marcado → cookie persistente de larga duración + JWT de larga duración.
2. **Default: desmarcado** (cookie de sesión). Recordar es una decisión consciente del usuario.
3. **Duración "recordar": 30 días** (configurable por env).

## Arquitectura

### 1. Backend — `app/core/config.py`

Agregar a `Settings`:
```python
remember_session_days = int(os.getenv("REMEMBER_SESSION_DAYS", "30"))
```

### 2. Backend — `app/routers/auth.py`

- Import `Form`: `from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status`.
- `login_for_access_token` recibe un parámetro extra `remember: bool = Form(False)` (FastAPI lo combina con el `OAuth2PasswordRequestForm`).
- Lógica de expiración/cookie:
  - Si `remember`:
    - `expires = timedelta(days=settings.remember_session_days)`
    - `cookie_max_age = settings.remember_session_days * 24 * 3600`
  - Si no:
    - `expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)` (12h, comportamiento actual del JWT)
    - `cookie_max_age = None` → cookie de **sesión** (se omite `max_age`/`expires` en `set_cookie`).
  - `access_token = create_access_token(data={...}, expires_delta=expires)`.
  - `set_cookie` con los kwargs comunes (`httponly`, `samesite`, `secure`), agregando `max_age=cookie_max_age` **solo cuando no es None** (cookie de sesión = sin `max_age`).
- `/me` y `/logout` no cambian.

### 3. Frontend — `web/src/features/auth/pages/LoginPage.tsx`

- Nuevo estado `const [remember, setRemember] = useState(false);` (default **false**).
- Un checkbox "Recordar sesión" bajo el campo de contraseña, ligado a `remember`.
- En el `fetch` de login, incluir `remember` en el body: `new URLSearchParams({ username: email, password, remember: String(remember) })`. FastAPI parsea `"true"`/`"false"` a bool.

### 4. Cobertura del AC

| Criterio | Cómo se cubre |
|----------|---------------|
| Definir si se permite "recordar sesión" | Checkbox explícito en login. |
| Si no está habilitado, pedir login | Default desmarcado → cookie de sesión → al cerrar el navegador, `/me` da 401 → login. |
| Si está habilitado, debe ser explícito | El usuario marca conscientemente → cookie 30 días. |
| No entrar directo sin control | Se elimina la persistencia silenciosa; persistir es decisión del usuario. |

## Fuera de alcance (YAGNI)

- Refresh tokens / rotación de tokens.
- Aviso pre-expiración del JWT o timeout por inactividad.
- Revocación individual de tokens (sigue vía `activo` —que `/me` respeta— o rotación de `SECRET_KEY`).

## Riesgos y verificación

- **Sin test suite** (CLAUDE.md): backend `python3 -m py_compile`; frontend `cd web && npm run build`. Verificación manual del flujo de cookie en el navegador.
- **Seguridad:** un token "recordado" de 30 días es de larga vida y no revocable individualmente (solo `activo` + rotación de `SECRET_KEY`). Aceptable para este sistema mono-tenant interno. La cookie sigue `HttpOnly`/`samesite=lax`; en producción debe ir con `COOKIE_SECURE=true` (ya advertido por config).
- **Cambio de comportamiento:** hoy todos quedan recordados 12h; tras este cambio, sin marcar el checkbox la sesión termina al cerrar el navegador. Es el objetivo del AC; comunicar a los usuarios si hace falta.
- **Sin migración** ni cambios de esquema.
