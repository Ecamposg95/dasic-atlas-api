# Arquitectura

## Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2.x, Alembic, `psycopg` (Postgres driver), Pydantic v2.
- **DB**: PostgreSQL 15+. Solo Postgres — no SQLite ni mocks.
- **Frontend**: SSR con Jinja2 templates + Tailwind CDN (Play) + Alpine.js + ECharts (sólo dashboard).
- **Auth**: JWT con `python-jose`, cookie httponly `access_token` + bearer header opcional.
- **Externos**: Banxico SIE API (TC oficial), `open.er-api.com` (fallback FX), Anthropic SDK (sugerencias IA), SMTP stdlib.
- **Deploy**: Railway (Postgres + servicio web). Auto-deploy desde `main`.

## Estructura de carpetas

```
app/
  main.py            # Entry point: crea FastAPI, monta /static, registra middlewares y routers
  core/
    config.py        # Settings con pydantic, valida DATABASE_URL/SECRET_KEY
    lifespan.py      # @asynccontextmanager: create_all + run_all_seeds (incluye backfill DDL)
    logging.py
  db/
    base.py          # declarative_base
    session.py       # engine, SessionLocal, get_db (dep injection)
    seeds.py         # _BACKFILL_DDL idempotente + seed_super_admin + run_seed(context/)
  models/            # SQLAlchemy ORM, particionado por dominio
    enums.py         # RolUsuario, EstatusOrden, TipoMovimiento, TipoLineaCotizacion, TipoMovimientoStock
    users.py         # Usuario
    catalog.py       # Producto, Promocion
    clients.py       # Cliente, Proveedor (Cliente.creado_por_id para owner-scoping)
    sales.py         # OrdenVenta, DetalleOrden (DetalleOrden.tipo_linea: catalogo|fantasma|servicio)
    purchases.py     # OrdenCompra, DetalleCompra (cotizacion_id → vinculo a OrdenVenta)
    finance.py       # TransaccionCliente, TransaccionProveedor
    quote_events.py  # QuoteEvent (audit log de email/WhatsApp/IA)
    inventory.py     # MovimientoStock (auditoría de cambios de stock)
    fx.py            # TipoCambioDia (cache de TC USD/MXN)
  schemas/           # Pydantic; mismos dominios que models/
  routers/           # FastAPI routers, prefijo /api/<modulo>
    auth.py          # /login, /logout, /me (capabilities)
    usuarios.py      # CRUD usuarios + reset password (admin only)
    productos.py     # CRUD productos + import CSV/XLSX + ajuste stock
    ventas.py        # cotizaciones + ventas + sugerir-oc/generar-oc + PDF
    clientes.py      # CRUD clientes (filtra por creado_por_id si rol ventas)
    compras.py       # OCs + recibir
    inventario.py    # /movimientos, /disponibilidad, /liberar-vencidas
    dashboard.py     # /hero, /pipeline, /tendencia, /alertas, /tops, /heatmap (role-aware)
    fx.py            # /usd-mxn, /refresh
    gastos.py
    admin.py         # /seed-context (solo admin)
  services/
    fx_service.py    # get_or_fetch(db) Banxico → fallback open.er-api → cache
    stock_service.py # aplicar_movimiento, reservar/liberar, consumir_reservas_a_salida
    auto_oc_service.py # previsualizar_ocs, generar_ocs (agrupa por proveedor)
    email_service.py # SMTP enviar PDF
    ai_service.py    # Anthropic SDK
    __init__.py      # UserService (hash + verify password con bcrypt)
  security/
    jwt.py           # create_access_token, get_current_user, RoleChecker, allow_admin etc
    permissions.py   # MATRIZ central + can/require/scope_query_by_owner + capabilities_for
  templates/         # Jinja2 SSR
    base.html        # layout: sidebar role-aware, header, $store.user
    dashboard.html cotizador.html inventario.html clientes.html compras.html
    usuarios.html seguimiento.html reportes.html gastos.html login.html
  static/css/
    cotizador.css
  data/
    marca_abreviaturas.json  # taxonomía DASIC (35 prefijos AB*) — generada por el seed
context/              # PDFs/Excel reales DASIC (referencia visual + fuente del seed)
docs/
  superpowers/specs/  # specs técnicos por feature
  superpowers/plans/  # planes de implementación
  onboarding/         # este manual
migrations/versions/  # Alembic
scripts/
  import_context_data.py  # idempotente; siembra productos, clientes, cotizaciones reales
```

## Bootstrap (qué pasa al arrancar)

`uvicorn app.main:app` → carga `app/main.py`:

1. `configure_logging()` + `get_settings()` (valida `DATABASE_URL`, `SECRET_KEY`).
2. Crea `app = FastAPI(lifespan=lifespan)`.
3. Mount `/static`, configura templates Jinja2.
4. Middlewares: `ProxyHeadersMiddleware` (HTTPS detrás del proxy de Railway), CORS.
5. Registra routers: auth, productos, ventas, clientes, compras, usuarios, gastos, dashboard, fx, inventario, admin.
6. Lifespan startup (`app/core/lifespan.py`):
   - `Base.metadata.create_all()` — crea tablas que falten.
   - `run_all_seeds(db)` →
     - `run_backfill_ddl()` — `ALTER TABLE … ADD COLUMN IF NOT EXISTS …` para columnas nuevas (puente cuando Railway no corre alembic).
     - `seed_super_admin()` — crea `admin@dasic.com / admin123` si la tabla está vacía.
     - `run_seed(db)` — siembra productos/clientes/proveedores/cotizaciones desde `context/`. Default ON; desactivar con `SEED_CONTEXT_DISABLED=1`.

## Auth

- POST `/api/auth/login` (form): valida con bcrypt, emite JWT (HS256), setea cookie httponly `access_token` + responde JSON con `access_token`.
- Cualquier ruta protegida: `Depends(get_current_user)` toma el JWT del header `Authorization: Bearer …` o de la cookie.
- Rutas SSR (`/dashboard`, `/cotizador`, etc.) usan `_protected_view` factory en `app/main.py` que redirige a `/` si no hay JWT válido.
- Logout: POST `/api/auth/logout` borra cookie y redirige a `/`.

## Variables de entorno

Ver `.env.example`. Mínimo:

| Var | Default | Notas |
|---|---|---|
| `DATABASE_URL` | — | `postgresql+psycopg://user:pass@host:5432/db`. Requerida. |
| `SECRET_KEY` | — | JWT signing. Requerida. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 720 | 12h por default |
| `TOKEN_COOKIE_NAME` | `access_token` | |
| `COOKIE_SECURE` | `false` | poner `true` en prod sobre HTTPS |
| `BANXICO_TOKEN` | — | opcional, gratis. Sin él usa fallback |
| `SMTP_HOST/PORT/USER/PASS` | — | opcional, para envío de PDF |
| `ANTHROPIC_API_KEY` | — | opcional, para sugerencias IA |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | |
| `ALLOWED_ORIGINS` | `*` | CSV |
| `SEED_CONTEXT_DISABLED` | — | `1` para apagar el seed automático |

## Modelos clave (relaciones)

```
Usuario ──(1:N)── OrdenVenta (vendedor_id)
Cliente ──(1:N)── OrdenVenta (cliente_id)
Cliente.creado_por_id → Usuario (1:N) [para owner scoping VENTAS]
OrdenVenta ──(1:N)── DetalleOrden (orden_id)
DetalleOrden.producto_id → Producto (nullable: línea fantasma/servicio)
DetalleOrden.proveedor_sugerido_id → Proveedor (línea fantasma)
Producto.proveedor_principal_id/alterno_id → Proveedor
Proveedor ──(1:N)── OrdenCompra
OrdenCompra.cotizacion_id → OrdenVenta (auto-OC)
Producto ──(1:N)── MovimientoStock (audit trail)
TipoCambioDia (1 row/día) — cache USD→MXN
```

Detalles en cada `app/models/<dominio>.py`.
