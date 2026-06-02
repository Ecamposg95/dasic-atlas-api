# Recordar sesión (política de sesión) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un checkbox explícito "Recordar sesión" en el login que controla si la cookie es persistente (30 días) o de sesión (se borra al cerrar el navegador), default desmarcado.

**Architecture:** El endpoint de login recibe `remember` (Form); con él, JWT y cookie son de larga duración; sin él, JWT 12h y cookie de sesión (sin max_age). El frontend agrega el checkbox y lo manda en el body form-urlencoded. Sin migración.

**Tech Stack:** FastAPI (OAuth2PasswordRequestForm) + JWT en cookie HttpOnly; React 18 + Vite + TS.

**Verificación (este repo NO tiene suite de tests — CLAUDE.md):** backend `python3 -m py_compile`; frontend `cd web && npm run build`. Verificación manual del flujo de cookie en navegador.

**Referencia de diseño:** `docs/superpowers/specs/2026-06-01-recordar-sesion-design.md`.

---

## Fase 1 — Backend

### Task 1: Config + login con `remember`

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/routers/auth.py`

- [ ] **Step 1: Agregar la config `remember_session_days`**

En `app/core/config.py`, justo después de la línea `access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))`, agregar:

```python
    remember_session_days = int(os.getenv("REMEMBER_SESSION_DAYS", "30"))
```

- [ ] **Step 2: Importar `Form` en auth.py**

En `app/routers/auth.py`, cambiar:
```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
```
por:
```python
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
```

- [ ] **Step 3: Reemplazar la firma y el cuerpo de `login_for_access_token`**

Reemplazar la función `login_for_access_token` completa por:

```python
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = UserService.get_user_by_email(db, form_data.username)
    if not user or not UserService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrecto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # "Recordar sesión": cookie persistente de larga duración. Sin él: JWT de
    # 12h y cookie de SESIÓN (sin max_age → el navegador la borra al cerrarse).
    if remember:
        access_token_expires = timedelta(days=settings.remember_session_days)
        cookie_max_age = settings.remember_session_days * 24 * 3600
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        cookie_max_age = None

    access_token = create_access_token(
        data={
            "sub": user.email,
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )

    cookie_kwargs = dict(
        key=settings.token_cookie_name,
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    if cookie_max_age is not None:
        cookie_kwargs["max_age"] = cookie_max_age
    response.set_cookie(**cookie_kwargs)

    return {"access_token": access_token, "token_type": "bearer"}
```

- [ ] **Step 4: Verificar**

Run: `python3 -m py_compile app/core/config.py app/routers/auth.py`
Expected: sin salida (OK).

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/routers/auth.py
git commit -m "feat(auth): login con 'recordar sesión' — cookie persistente vs de sesión (US-031)"
```

---

## Fase 2 — Frontend

### Task 2: Checkbox "Recordar sesión" en `LoginPage`

**Files:**
- Modify: `web/src/features/auth/pages/LoginPage.tsx`

- [ ] **Step 1: Estado `remember`**

Junto a los otros `useState` del componente (donde están `email`, `password`, `showPass`), agregar:

```tsx
  const [remember, setRemember] = useState(false);
```

- [ ] **Step 2: Incluir `remember` en el body del login**

Localizar el `body: new URLSearchParams({ username: email, password }).toString(),` dentro del `fetch('/api/auth/login', ...)` y reemplazarlo por:

```tsx
        body: new URLSearchParams({ username: email, password, remember: String(remember) }).toString(),
```

- [ ] **Step 3: Agregar el checkbox bajo el campo de contraseña**

Localizar el cierre del bloque del campo Contraseña (el `</div>` que cierra el `<div>` contenedor del label "Contraseña" + input + botón mostrar/ocultar). Inmediatamente DESPUÉS de ese `</div>` (y antes del `<button>` de submit), agregar:

```tsx
            <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 accent-accent-glow"
              />
              Recordar sesión en este equipo
            </label>
```

- [ ] **Step 4: Verificar**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores TS.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/auth/pages/LoginPage.tsx
git commit -m "feat(auth): checkbox 'Recordar sesión' en el login (US-031)"
```

---

## Fase 3 — Build final + push

### Task 3: Build del SPA y push

- [ ] **Step 1: Build final**

Run: `cd web && npm run build`
Expected: `✓ built` sin errores; `app/static/dist/` regenerado.

- [ ] **Step 2: Commit del dist + push**

```bash
git add app/static/dist
git commit -m "build: recompila SPA (dist) — US-031 recordar sesión"
git push origin main
```

---

## Notas de verificación manual (post-deploy, recomendado)

- Login SIN marcar "Recordar sesión" → en DevTools → Application → Cookies, la cookie `access_token` debe aparecer como "Session" (sin Expires/Max-Age). Cerrar el navegador y reabrir → debe pedir login.
- Login CON "Recordar sesión" marcado → la cookie debe tener Max-Age ≈ 30 días. Cerrar y reabrir el navegador → entra directo.
- El checkbox viene desmarcado por defecto.
- Logout sigue funcionando (borra la cookie).
