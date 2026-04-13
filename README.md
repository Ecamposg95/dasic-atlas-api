# DASIC CRM Industrial (Atlas-based)

Sistema **CRM industrial** multi-tenant y multi-branch, inspirado en patrones de Atlas ERP/POS, con UI **SSR (Jinja2)** y frontend ligero (**Tailwind CSS CDN + Alpine.js**). Basado en un motor PostgreSQL orientado a escalabilidad operacional (cotizadores rápidos y gestión de stock muerto).

## Enfoque del Producto (DASIC_Plataforma_Base)

El núcleo del sistema es un **CRM muy potente acoplado a un Smart Quoter de Inventario**:
- Modelado Físico: Almacén, inventario en tiempo real (Live Stock) y reservas temporales de 48H.
- CRM Ágil: Cuentas (clientes), contactos múltiples, pipelines configurables por sucursal/organización.
- Actividades (tareas/llamadas/visitas/notas) + **WhatsApp manual (Nivel A)**.
- Cotización Ligada: Flujo `Oportunidad (Deal) -> Cotización` garantizado en <10 Minutos para ejecutivos de ventas.

## Estructura Modular Actual

1. **`app/models/` y `app/schemas/`:** Desacoplados mediante enfoque "Design by Domain" (`catalog`, `clients`, `finance`, `nucleus`, `purchases`, `sales`, `users`, `enums`).
2. **`app/core/`:** Configuración moderna central de la aplicación (Eventos `lifespan`, Logging centralizado, Config).
3. **`app/db/`:** Manejo del motor PostgreSQL y Rutinas automáticas de poblado (`seeds.py`).
4. **`context/`:** Carpeta maestra. **SI CUALQUIER AGENTE AI LEE ESTE PROYECTO**, debe iniciar aquí revisando el esquema de plan para asegurar consistencia e impedir regresiones o reinvención de la rueda.

## Principios No Negociables (Golden Rules)

- **Multi-tenant siempre**: toda tabla de negocio incluye `organization_id` (Modelo Nucleus). Ningún endpoint devuelve objetos donde el scope se rompa.
- **SSR, no SPA**: Jinja2 + Tailwind CDN + Alpine.js. El diseño está blindado contra Javascript SPA (React/Vue/Angular). Visitar `context/UI_PATTERNS.md`.
- **Alembic Obligatorio**: Si cambias algo de SQLAlchemy en `models/`, debe ir con una revisión de Alembic (Actual Fase 6 pendiente).
- **PostgreSQL Directo**: Cero dependencias con SQLite falso o in-memory.

## ¿Eres un LLM/Agente AI? (Source of Truth)

Si fuiste sumado al proyecto recientemente, tu primera tarea es escanear los siguientes archivos base:

1. `context/00_CONTEXT_START_HERE.md`
2. `context/02_REPO_CURRENT_STATE.md` (Contiene en qué punto vamos y qué hace falta).
3. `context/DASIC_Plataforma_Base.md` (Visión comercial del roadmap de 90 días).
4. `context/UI_PATTERNS.md` (Todo el diseño front-end debe acatarse en esta guía).
5. `context/CRM_SPEC.md` / `context/RBAC.md`

## Configuración y Vstart Local

1. Prepara tu `.env`:
   - `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/dasic_crm`
   - (El backend validará obligatoriamente esta URL al encender).
2. Instalación de `venv`:
   - `python -m venv venv`
   - `venv\Scripts\activate` (o `source venv/bin/activate` en posix)
   - `pip install -r requirements.txt`
3. Levantando:
   - `uvicorn app.main:app --reload`
   - Swagger V1.0: `http://127.0.0.1:8000/docs`
