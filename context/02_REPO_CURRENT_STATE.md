# Estado Actual del Repo (Dasic_Atlas_api)

Este repo hoy es un prototipo funcional con FastAPI + SQLAlchemy + Jinja2 templates y Tailwind via CDN, pero **no** esta aun alineado a la arquitectura multi-tenant Atlas.

## Estructura actual (real)

Ruta principal:

- `app/main.py`

Base de datos:

- `app/database.py` define `SQLALCHEMY_DATABASE_URL = "sqlite:///./cotizador_pro.db"` (hardcoded)
- DB file presente: `app/cotizador_pro.db`

Auth:

- JWT HS256 con `SECRET_KEY` hardcoded en `app/auth.py`
- Login API: `POST /api/auth/login` en `app/routers/auth.py`
- UI usa `localStorage` para guardar token (ver `app/templates/login.html`)

Routers API:

- `app/routers/auth.py`
- `app/routers/productos.py`
- `app/routers/ventas.py`
- `app/routers/clientes.py`
- `app/routers/compras.py`
- `app/routers/usuarios.py`
- `app/routers/gastos.py`

SSR templates (Jinja2):

- `app/templates/login.html`, `dashboard.html`, `cotizador.html`, `seguimiento.html`, `inventario.html`, `clientes.html`, `compras.html`, `gastos.html`, `reportes.html`, `usuarios.html`

Static:

- `app/static/js/navbar.js` (sidebar/header/footer)
- `app/static/js/cotizador.js`, `utils.js`

## Riesgos/inconsistencias actuales

1. Imports: `app/main.py` importa `database`, `models`, `services` como modulos top-level; con `uvicorn app.main:app` esto suele fallar si no se ejecuta desde el cwd correcto.
1. Password hashing: `app/services.py` usa `argon2`, pero `requirements.txt` declara `passlib[bcrypt]`.
1. Seguridad: `SECRET_KEY` hardcoded; CORS `allow_origins=["*"]`.
1. No hay multi-tenancy: no existe `Organization`, `Branch`, ni `organization_id` en tablas.

## Objetivo de migracion

Convertir el proyecto a:

- PostgreSQL directo por `DATABASE_URL`
- Multi-tenant (UUID org) + multi-branch
- RBAC + visibilidad por asignacion
- CRM como modulo central (múltiples pipelines)
- Auth SSR con cookies HttpOnly
- Alembic para migraciones
