# Onboarding DASIC ERP

Manual para desarrolladores nuevos, partners de implementación y operadores que se integren al proyecto **Dasic_Atlas_api** (CRM/ERP B2B de DASIC, automatización industrial mexicana).

## Orden recomendado de lectura

| # | Documento | Para quién | Tiempo |
|---|---|---|---|
| 1 | [10_project_overview.md](10_project_overview.md) | Todos | 5 min |
| 2 | [20_architecture.md](20_architecture.md) | Devs, partners | 15 min |
| 3 | [30_dev_workflow.md](30_dev_workflow.md) | Devs | 20 min (ejecutar setup) |
| 4 | [40_funcional_flujos.md](40_funcional_flujos.md) | Devs, operadores | 15 min |
| 5 | [50_glossary.md](50_glossary.md) | Todos (referencia rápida) | 3 min |
| 6 | [60_troubleshooting.md](60_troubleshooting.md) | Devs (cuando algo falla) | bajo demanda |
| 7 | [70_rbac_y_roles.md](70_rbac_y_roles.md) | Devs + operadores | 10 min |

## Por tipo de persona

- **Dev nuevo**: leé 1→2→3 y levantá el proyecto local. Después 4 y 7. Cuando algo falle, 6.
- **Partner de implementación**: 1, 4, 7. Pasale 60_troubleshooting al equipo de soporte.
- **Operador (admin/gerente/ventas/almacén)**: 1, 4, 7. La sección "Tu rol" en cada documento te da el subset.

## Documentos relacionados

- Especificaciones técnicas: `docs/superpowers/specs/` (RBAC, cotizador robusto, inventario, etc.)
- Planes de implementación: `docs/superpowers/plans/`
- Documentación general del proyecto: `CLAUDE.md` (raíz) y `context/` (referencia funcional + PDFs reales).
