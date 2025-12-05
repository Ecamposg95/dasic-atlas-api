# 📄 Cotizador ERP

**Sistema de Cotizaciones y Órdenes de Compra** diseñado para gestionar propuestas comerciales, controlar compromisos con proveedores y monitorear el estado de cuenta de clientes dentro de un flujo ERP ligero pero potente.

El objetivo es centralizar los procesos comerciales clave: **cotizar, convertir en orden, registrar pagos y visualizar adeudos**, todo bajo una arquitectura modular y escalable.

---

## 🚀 Objetivo del Proyecto
Crear una plataforma ERP enfocada en **cotizaciones, órdenes de compra y estados de cuenta**, permitiendo a empresas administrar de forma profesional todo su ciclo comercial y financiero básico.

---

## 📋 Características Principales

### 🧾 Módulo de Cotizaciones
- Generación de cotizaciones profesionales (PDF).
- Cotizaciones multi-divisa (MXN / USD).
- Ajustes de precios por partida.
- Margen de utilidad automático.
- Conversión de cotización → orden de compra con un clic.

### 🛒 Órdenes de Compra
- Control de compras a proveedores.
- Productos "fantasma" (creación rápida desde la OC).
- Actualización automática del inventario.
- Registro de pagos a proveedores.
- Historial completo de compras.

### 💳 Estados de Cuenta (Clientes)
- Registro de abonos.
- Panel visual de adeudos.
- Historial financiero por cliente.
- Conversión automática de órdenes a cuentas por cobrar.

### 🔐 Seguridad y Roles
- Autenticación JWT.
- Roles sugeridos:
  - **Admin** — Control total del sistema.
  - **Ventas** — Cotizaciones y cuentas por cobrar.
  - **Compras** — Órdenes de compra y proveedores.

---

## 🛠️ Stack Tecnológico

- **Backend:** FastAPI (Python 3.10+)
- **ORM:** SQLAlchemy
- **Base de datos:** SQLite (fácil de migrar a PostgreSQL/MySQL)
- **Seguridad:** JWT, Passlib
- **Frontend:** HTML + JS + Tailwind CSS
- **Generación de PDFs:** fpdf2

---

## 📂 Estructura del Proyecto

```text
cotizador-erp/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── services/
│   │   ├── cotizaciones_service.py
│   │   ├── ordenes_service.py
│   │   └── clientes_service.py
│   ├── routers/
│   │   ├── cotizaciones.py
│   │   ├── ordenes.py
│   │   ├── clientes.py
│   │   ├── proveedores.py
│   │   └── auth.py
│   ├── templates/
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── cotizaciones.html
│   │   ├── ordenes.html
│   │   └── clientes.html
│   ├── static/
│       ├── js/
│       └── css/
└── requirements.txt
```

---

## ⚙️ Instalación

```bash
git clone https://github.com/tu-usuario/cotizador-erp.git
cd cotizador-erp
```

### Crear entorno virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Instalar dependencias
```bash
pip install -r requirements.txt
```

### Ejecutar servidor
```bash
uvicorn app.main:app --reload
```

Documentación disponible en:
- Swagger: http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

---

## 📦 Dependencias (requirements.txt)

```
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
fpdf2
jinja2
```

---

Desarrollado para **Smart Site Company / DASIC**.
