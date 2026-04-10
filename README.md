# DASIC CRM Industrial (Atlas-based)

Sistema **CRM industrial** multi-tenant y multi-branch, inspirado en patrones de Atlas ERP/POS, con UI **SSR (Jinja2)** y frontend ligero (**Tailwind CSS CDN + Alpine.js**). El cotizador vive como capacidad del CRM (cotizaciones ligadas a oportunidades y cuentas).

## Enfoque del Producto

El nucleo del sistema es un **CRM muy potente**:

- Cuentas (clientes) + contactos + sitios/ubicaciones (plantas)
- Multiples pipelines por organizacion
- Oportunidades (deals) por pipeline/etapa con ownership y asignacion
- Actividades (tareas/llamadas/visitas/notas) + **WhatsApp manual (Nivel A)**
- Timeline/auditoria funcional (eventos de negocio)
- Cotizaciones ligadas a oportunidades (fase siguiente)

## Principios No Negociables

- **Multi-tenant siempre**: toda tabla de negocio incluye `organization_id` y toda query filtra por `organization_id`.
- **Multi-branch**: usuarios pueden ser globales (HQ) o branch-scoped; si son branch-scoped, su visibilidad se limita a su `branch_id` salvo roles de nivel gerente+.
- **SSR, no SPA**: Jinja2 + Tailwind CDN + Alpine.js. No se introduce routing client-side.
- **RBAC + visibilidad por asignacion**: endpoints aplican roles y filtros de ownership/asignacion.
- **PostgreSQL directo**: sin fallback a SQLite.
- **Alembic obligatorio**: migraciones para evolucion de esquema.
- **Auth SSR con cookies HttpOnly**: JWT en cookie HttpOnly (evitar `localStorage`).

## Stack Tecnologico

- Backend: FastAPI
- ORM: SQLAlchemy (2.x)
- DB: PostgreSQL
- Migraciones: Alembic
- SSR: Jinja2
- Frontend: Tailwind CSS (CDN) + Alpine.js
- Lenguaje: Python puro

## Documentacion (Source of Truth)

Lee primero:

- `context/00_CONTEXT_START_HERE.md`
- `context/CRM_SPEC.md`
- `context/RBAC.md`
- `context/ARCHITECTURE.md`
- `context/API_CONVENTIONS.md`
- `context/ROADMAP.md`

Referencia upstream:

- `context/01_ATLAS_REFERENCE.md`

## Requisitos

- Python 3.10+
- PostgreSQL (recomendado 14+)

## Configuracion (.env)

Crear `.env` (ejemplo):

- `DATABASE_URL=postgresql+psycopg://postgres:toor@localhost:5432/dasi_crm_local`
- `SECRET_KEY=change-me`
- `ACCESS_TOKEN_EXPIRE_MINUTES=720`

Notas:

- `SECRET_KEY` es obligatorio (no hardcode).
- En SSR el JWT se emite en cookie HttpOnly.

## Ejecutar (Desarrollo)

1. Crear venv e instalar dependencias
   - `python -m venv venv`
   - `source venv/bin/activate`
   - `pip install -r requirements.txt`

2. Migraciones (Alembic)
   - `alembic upgrade head`

3. Levantar servidor
   - `uvicorn app.main:app --reload`

4. Abrir
   - UI: `http://127.0.0.1:8000/`
   - Swagger: `http://127.0.0.1:8000/docs`

## Acceso Inicial (Prototipo Privado)

En modo prototipo, el sistema crea un administrador inicial:

- Email: `admin@dasic.com`
- Password: `admin123`

Uso recomendado: solo en ambientes de prueba/privados.

## Multi-Tenancy (Headers)

Convencion de headers para API:

- `X-Organization-ID: <uuid>` (obligatorio)
- `X-Branch-ID: <uuid>` (opcional)

Reglas:

- El `X-Organization-ID` se valida contra el `org_id` del JWT.
- Si el usuario es branch-scoped, `X-Branch-ID` debe coincidir con su `branch_id` (o se rechaza).

## RBAC (Roles)

Tenant roles (cerrados):

- `DUEÑO`
- `ADMINISTRADOR`
- `GERENTE_COMERCIAL`
- `VENTAS`
- `CRM`
- `AUDITOR`
- `LECTOR`

La matriz detallada y reglas de visibilidad estan en `context/RBAC.md`.

## Estado del Proyecto

Este repo esta en transicion a la arquitectura objetivo. La especificacion y roadmap estan en `context/`.
