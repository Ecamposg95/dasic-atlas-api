# Registro de riesgos

> Auditoría Task Pack 00 · 2026-08-03 · **estados revisados 2026-11-23**. Sistema **en producción con autodeploy desde `main`** — ese es el contexto de todo riesgo.

## Críticos

| ID | Riesgo | Mitigación |
|---|---|---|
| R1 | ~~**Todo push a `main` despliega a producción sin tests.**~~ **Mitigado (2026-08-05).** CI corre pytest sobre PostgreSQL 16 + typecheck + vitest + build en cada push y PR, y existe environment `staging` con base propia. **Residual:** CI no bloquea el deploy —Railway despliega en paralelo— y staging aún apunta a `main` (paso manual pendiente, ver backlog P0 "Operativos"; la rama `staging` va 73 commits detrás de `main` al 2026-11-23). | Mantener commits pequeños; validar en staging antes de mergear; smoke manual post-deploy. |
| R2 | ~~**Cero cobertura de tests** sobre lógica de dinero~~ **Parcialmente mitigado.** El motor de cálculo del cotizador está cubierto (58 tests de vitest, valores derivados a mano) y la concurrencia de remisiones también. **Actualización 2026-11-23:** totales, redondeo, fechas, stock y cobranza del backend ya tienen pruebas (185 funciones de prueba sobre PostgreSQL en CI). **Residual:** no hay suite E2E del golden path, y CRM y compras siguen sin pruebas dedicadas. | Montar las pruebas del área **antes** de refactorizarla, no después. |
| R3 | **Esquema de DB con doble vía** (Alembic + `_BACKFILL_DDL` + `create_all`); Railway no corre Alembic. Columna nueva sin backfill → 500 en todos los endpoints que carguen la fila. | Regla vigente: toda columna en tabla existente = migración + entrada `_BACKFILL_DDL` + re-export. No introducir cambios de esquema en la fase visual salvo indispensables. |

## Importantes

| ID | Riesgo | Mitigación |
|---|---|---|
| R4 | ~~**Endpoints sin autenticación.**~~ **Cerrado (2026-08).** Los seis endpoints responden 401 sin credenciales (re-verificado contra producción el 2026-11-23) y un barrido de todas las rutas montadas lo vigila en la suite. *Hallazgo original:* verificado contra producción: `GET /api/compras/proveedores`, `GET /api/compras/`, `GET /api/compras/historial` y `GET /api/compras/{id}/imprimir` responden **200 sin credenciales**, y `POST /api/compras/proveedores` es una **escritura** abierta. También `GET /api/clientes/{id}/pdf-estado-cuenta`. No es un fallo general: `/api/remisiones/` y `drop-all-tables` sí responden 401. | Hecho. Mantener el barrido de rutas en verde al agregar endpoints. |
| R5 | ~~`SECRET_KEY` puede rotar entre deploys (si no está fijada en Railway) → sesiones invalidadas en cada release del rediseño.~~ **Cerrado.** La variable está definida en los servicios de `production` y `staging` (verificado 2026-11-23). | Nada pendiente. |
| R6 | Migración masiva slate→tokens puede romper contraste/light-mode en páginas no revisadas. | Migrar por feature (commit por página), QA visual light+dark por página; guardrail del prompt: no reemplazar todos los estilos en un cambio masivo. |
| R7 | Documentación contradictoria (`context/` legacy: Next.js/Prisma hipotético, Jinja retirado, multi-tenant que ya no existe) puede inducir a agentes/devs a decisiones erróneas. | `docs/current-state/` (este paquete) como fuente única del estado; marcar/archivar legacy en Task Pack 17. |
| R8 | SaaS: la expectativa "DASIC como primer tenant" choca con la realidad mono-tenant (multi-tenancy retirada en `20260429_01`). Re-tenantizar la DB es proyecto mayor. | Etapa actual: tenant-config/branding/feature-flags **frontend + config runtime** (Task Pack 14 ligero); multi-tenancy real documentada como roadmap, no ejecutada ahora. |

| R12 | **Todo el workspace de Railway puede apagarse a la vez.** El 2026-11-22 ~08:03 UTC Railway retiró todos los servicios del workspace (API y Postgres de `production` y `staging` incluidos) y los redesplegó el 2026-11-23 17:50 UTC: unas 34 horas de producción caída, sin aviso interno. Causa **no confirmada**; el patrón es el de una suspensión por facturación (el workspace tiene límite duro de uso de 30). Los datos sobrevivieron (volumen de Postgres). | Revisar Billing/Usage del workspace, subir o quitar el límite duro si fue la causa, y poner un monitor externo de disponibilidad sobre la URL de producción. |

## Deseables de vigilar

| ID | Riesgo | Nota |
|---|---|---|
| R9 | Modales grandes (OC/Producto) al migrarse a drawer/página pueden alterar flujos memorizados por usuarios. | Cambios opt-in, comunicar en demo. |
| R10 | Bundle: agregar librerías de UI pesadas (calendarios, gantt) contradice el presupuesto actual (~200 kB vendor-react). | Medir antes; preferir composición con primitivas propias. |
| R11 | `hello` y templates Jinja muertos generan superficie de confusión. | Retiro programado (Fase 5), no urgente. |

## Ambigüedades / dependencias externas

- ~~No hay entorno de staging conocido.~~ Existe el environment `staging` en Railway con base propia; falta apuntarlo a la rama `staging`.
- No hay acceso a screenshots/baseline visual desde este entorno (WSL headless) — pendiente Task Pack 01 con dev server.
- Falta confirmación del usuario sobre: nombre público del producto en UI neutra ("Atlas Industrial Services" vs "Atlas ONE"), y si la consola superadmin entra en el rediseño (hoy 0% tokens).
