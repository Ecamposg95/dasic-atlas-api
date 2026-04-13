# Estado Actual del Repo (Dasic_Atlas_api)

> **Actualizado:** 2026-04-13 (Post-Refactor Fases 1-3, 5)

Este repositorio base está alineado arquitectónicamente con Atlas a través de una refactorización modular. Actualmente estamos en la rama `develop` construyendo los esquemas multi-tenant y CRM-first, orientados a resolver los retos del blueprint comercial.

## Estructura Actual (Refactorizada)

**Core y Bootstrap:**
- `app/main.py`: Limpio (~90 líneas). Solo bootstrap de FastAPI, montado de SSR y middlewares.
- `app/core/lifespan.py`: Maneja los eventos de startup de manera moderna (reemplaza `@on_event`).
- `app/core/logging.py`: Configuración central de logging estructurado.

**Base de Datos y Modelos:**
- `app/db/session.py` (y `db/__init__.py`): Manejan el session engine de SQLAlchemy para PostgreSQL.
- `app/db/seeds.py`: Rutinas de backfill retroactivo de DDL y creación de tenant base en el startup.
- `app/models/`: Separado por dominio de negocio (`nucleus.py`, `users.py`, `catalog.py`, `clients.py`, `sales.py`, `purchases.py`, `finance.py`, `enums.py`).
- `app/schemas/`: Espejeado con los subdominios de los modelos para Pydantic.

**API y SSR:**
- `app/routers/`: Mantienen endpoints por áreas (próximo a incorporar capa de Repositories).
- `app/templates/`: Vistas de SSR con Jinja2 (dashboard, cotizador, inventario, clientes, etc).
- `app/static/`: Assets crudos CSS/JS. **Se usa Tailwind CDN y Alpine.js** globalmente.

## Cumplimiento con DASIC_Plataforma_Base:

Se ha consolidado el documento `context/DASIC_Plataforma_Base.md` que detalla el Plan de Operaciones a 90 días:
1. **Live Stock:** Kardex, inventario en tiempo real, banderas de stock crítico.
2. **Smart Quoter:** Generar cotizaciones en < 10 mins con reservas por 48 horas de stock.
3. **Dashboard:** Para Dirección General y KPIs.

## Riesgos y Siguientes Fases (Pendientes)

1. **Capa Repository (Fase 4):** Aún hay acoplamiento de SQLAlchemy en los `routers/`. Es necesario crear `app/repositories/` para desacoplar el acceso a la DB.
2. **Alembic (Fase 6):** El DDL manual (`ALTER TABLE`) manejado desde `db/seeds.py` necesita migrarse oficialmente al mapeo por Alembic.
3. **CRM Engine MVP (Fase 7):** Entidades como `Deal`, `Pipeline`, `Activity` faltan por crearse bajo el motor oficial.
4. **Cotizador Inteligente & Reserva (Fase 8):** Implementar la lógica del blueprint operativo para enganchar oportunidades de CRM directo a apartados físicos.
