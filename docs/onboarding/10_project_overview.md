# Project overview

## Qué es DASIC ERP

Aplicación web SSR (server-side rendered con Jinja2 + Alpine + Tailwind) que digitaliza el flujo comercial de **DASIC**, una empresa mexicana de automatización industrial. Vende productos de marcas como Allen Bradley, Schneider, Phoenix Contact, SMC, Siemens, Finder, AutomationDirect a clientes industriales (Vitracoat, Dimeint, etc).

## Problema que resuelve

DASIC operaba con archivos Excel para cotizar y un cuaderno físico para inventario. La conversión cot→venta y el control de stock se perdía entre archivos. La aplicación centraliza:

- **Cotizaciones** con costo+utilidad multi-moneda (MXN/USD), TC tomado de Banxico (oficial mexicano).
- **OCs automáticas** a proveedores cuando hay faltantes (auto-OC agrupada por proveedor).
- **Inventario en tiempo real** con tres números clave: Físico / Reservado / Disponible (lo reservado se descuenta al cotizar y se libera al cancelar).
- **Trazabilidad de movimientos**: cada cambio de stock deja una fila en `movimientos_stock` con motivo, usuario y referencia.
- **Multi-rol**: cada usuario ve y puede hacer sólo lo que su rol permite.

## Personas (roles)

| Rol | Quién es | Qué hace en el sistema |
|---|---|---|
| **Administrador** | Dueño / IT | Todo: usuarios, configuración, productos, costos. |
| **Gerente Comercial** | Supervisa al equipo de ventas | Ve dashboard de equipo, gestiona todas las cotizaciones, autoriza OCs. |
| **Ventas** | Vendedor de campo | Crea cotizaciones para sus clientes, las da seguimiento, las convierte en venta. Sólo ve lo suyo. |
| **Operativo (almacén)** | Encargado del almacén | Recibe OCs, ajusta stock, hace inventarios físicos. No ve costos al cotizar; ve costo de compra. |

## Módulos

Cada módulo vive en su `app/templates/<nombre>.html` con su `app/routers/<nombre>.py` y, cuando aplica, su servicio en `app/services/`.

| Módulo | Template | Router | Servicio |
|---|---|---|---|
| **Dashboard premium** | `dashboard.html` | `dashboard.py` | (queries en el router) |
| **Cotizador** | `cotizador.html` | `ventas.py` | `auto_oc_service`, `stock_service` |
| **Seguimiento** | `seguimiento.html` | `ventas.py` (mismo router) | — |
| **Inventario** | `inventario.html` | `inventario.py` + `productos.py` | `stock_service` |
| **Clientes** | `clientes.html` | `clientes.py` | — |
| **Compras / OCs** | `compras.html` | `compras.py` | — |
| **Gastos** | `gastos.html` | `gastos.py` | — |
| **Reportes** | `reportes.html` | (en routers) | — |
| **Usuarios** | `usuarios.html` | `usuarios.py` | `UserService` |
| **FX (TC)** | (consumido por cotizador) | `fx.py` | `fx_service` |
| **Admin / seed** | (no template) | `admin.py` | `import_context_data` |

## Datos reales de referencia

`context/` tiene PDFs reales de DASIC (cotizaciones C-2604227, C-2604229; OC-2604001; remisión R-2604001) y una hoja Excel `LISTA_MATERIAL.xlsx` con 12 productos reales. El script `scripts/import_context_data.py` los siembra en la DB y son la guía visual de cómo deben verse los PDFs generados (`app/routers/ventas.py::PDF_TEMPLATE_VENTA`).

Los formatos de folio reales son:

- `C-YYMMNNN` cotización (ej. `C-2604227` = año 26, mes 04, secuencial 227).
- `V-YYMMNNN` venta (`C-…` se transforma a `V-…` al convertir).
- `OC-YYMMNNN` orden de compra.
- `R-YYMMNNN` remisión (modelo aún no implementado).
