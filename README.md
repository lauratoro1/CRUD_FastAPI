# FastAPI Persona CRUD (MySQL por defecto)

Proyecto de demostración con FastAPI + SQLAlchemy y estructura MVC para un CRUD de `Persona`. Usa MySQL por defecto y permite apuntar a otra base SQL mediante la variable de entorno `DATABASE_URL` (configurable en `.env`).

## Requisitos

- Python 3.10+ (recomendado 3.11)

## Instalación y ejecución

1. Crear entorno virtual e instalar dependencias:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales de MySQL
   # Por defecto: DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fastapi_demo
   ```

3. Ejecutar el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Documentación interactiva:
   - Swagger UI: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>

## Conexión a otras bases de datos

Edita `DATABASE_URL` en `.env`.
- MySQL: `mysql+pymysql://user:password@localhost:3306/mydb`

> Nota: Instala el driver correspondiente (psycopg2, PyMySQL, pyodbc, etc.).

## Ejemplo de `.env` (MySQL local)

```env
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/nombre_basedatos
```

## Endpoints principales

- `GET /health` → estado del servicio
- `POST /personas` → crear persona
- `GET /personas` → listar personas (`skip`, `limit`)
- `GET /personas/{id}` → obtener persona por ID
- `PUT /personas/{id}` → actualizar (parcial) persona
- `DELETE /personas/{id}` → eliminar persona

### Esquemas (JSON)

- Crear:
  ```json
  {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan.perez@example.com",
    "phone": "+57 3000000000",
    "birth_date": "1990-05-20",
    "is_active": true,
    "notes": "Cliente frecuente"
  }
  ```

- Actualizar (parcial):
  ```json
  {
    "email": "juan.perez2@example.com",
    "notes": "Actualizado"
  }
  ```

## Colección de Postman

Importa `FastAPI-CRUD-Demo.postman_collection.json` en Postman. Variables:

- `base_url` (por defecto `http://localhost:8000`)
- `persona_id` (por defecto `1`)

## Notas

- Las tablas se crean automáticamente al iniciar (solo con fines de demo).
- Asegúrate de crear la base de datos en MySQL y de que el usuario tenga permisos (por ejemplo, `CREATE DATABASE fastapi_demo;`).

## Estructura MVC

- `app/models/` → modelos SQLAlchemy (por ejemplo, `persona.py`).
- `app/views/` → esquemas Pydantic (por ejemplo, `persona.py`).
- `app/controllers/` → routers/controladores FastAPI (por ejemplo, `persona_controller.py`).

## Pruebas rápidas (curl)

```bash
# Health
curl -s http://127.0.0.1:8000/health

# Crear persona
curl -s -X POST http://127.0.0.1:8000/personas \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name":"Juan",
    "last_name":"Perez",
    "email":"juan.perez@example.com",
    "phone":"+57 3000000000",
    "birth_date":"1990-05-20",
    "is_active":true,
    "notes":"Cliente frecuente"
  }'

# Listar
curl -s http://127.0.0.1:8000/personas

# Obtener por ID
curl -s http://127.0.0.1:8000/personas/1

# Actualizar parcial
curl -s -X PUT http://127.0.0.1:8000/personas/1 \
  -H 'Content-Type: application/json' \
  -d '{"email":"juan.perez2@example.com","notes":"Actualizado"}'

# Eliminar
curl -s -X DELETE http://127.0.0.1:8000/personas/1 -i

## Detener el servidor

- Si lo iniciaste en la misma terminal: usa `CTRL+C`.
- Si corre en background, puedes cerrar esa terminal o matar el proceso de uvicorn (`pkill -f uvicorn`).

```

# FastAPI Persona CRUD - Laboratorio 1

Proyecto de demostración con FastAPI + SQLAlchemy y estructura MVC para un CRUD de `Persona`. Incluye **9 endpoints requeridos** y **6 endpoints extras** para analítica de datos.

---

## 👥 Integrantes y Distribución de Trabajo

### Juan David Garcia Hernandez 

| # | Servicio | Endpoint | Método | Descripción |
|---|----------|----------|--------|-------------|
| 1 | Reset | `/personas/reset` | DELETE | Eliminar todos los registros |
| 2 | Poblar | `/personas/poblar` | POST | Carga masiva con Faker |
| 3 | Dominios | `/personas/estadisticas/dominios` | GET | Conteo por dominio de email |
| 4 | Edad | `/personas/estadisticas/edad` | GET | Estadísticas de edad |
| 5 | Buscar | `/personas/buscar/{termino}` | GET | Buscador general |

**Archivos modificados:** `persona_controller.py`, `persona_service.py`, `views/persona.py`

---

### Laura Maria Toro Montoya 

| # | Servicio | Endpoint | Método | Descripción |
|---|----------|----------|--------|-------------|
| 6 | Activos | `/personas/reporte/activos` | GET | Reporte de usuarios activos |
| 7 | Cumpleaños | `/personas/cumpleanios/mes/{numero_mes}` | GET | Cumpleaños del mes |
| 8 | Desactivar | `/personas/bulk/desactivar` | PATCH | Desactivación masiva |
| 9 | CSV | `/personas/exportar/csv` | GET | Exportar a CSV |
| 10 | % Activos | `/personas/analitica/activos-porcentaje` | GET | Porcentaje activos/inactivos (extra) |

**Archivos modificados:** `persona_controller.py`, `persona_service.py`, `views/persona.py`

---

### Julián David Hernández Grisales 

| # | Servicio | Endpoint | Método | Descripción |
|---|----------|----------|--------|-------------|
| 11 | Rangos Edad | `/personas/analitica/rangos-edad` | GET | Distribución por rangos de edad (extra) |
| 12 | Top Dominios | `/personas/estadisticas/top-dominios` | GET | Top N dominios de email (extra) |
| 13 | Sin Notas | `/personas/analitica/sin-notas` | GET | Personas sin notas (extra) |
| 14 | Rango Fechas | `/personas/fechas/rango/{fecha_inicio}/{fecha_fin}` | GET | Búsqueda por rango de fechas (extra) |
| 15 | JSON | `/personas/exportar/json` | GET | Exportar a JSON (extra) |

**Archivos modificados:** `persona_controller.py`, `persona_service.py`, `views/persona.py`

---

## 📊 Resumen de Servicios

| # | Servicio | Endpoint | Método 
|---|----------|----------|--------|
| 1 | Reset | `/personas/reset` | DELETE |
| 2 | Poblar | `/personas/poblar` | POST | 
| 3 | Dominios | `/personas/estadisticas/dominios` | GET | 
| 4 | Edad | `/personas/estadisticas/edad` | GET | 
| 5 | Buscar | `/personas/buscar/{termino}` | GET | 
| 6 | Activos | `/personas/reporte/activos` | GET | 
| 7 | Cumpleaños | `/personas/cumpleanios/mes/{mes}` | GET | 
| 8 | Desactivar | `/personas/bulk/desactivar` | PATCH | 
| 9 | CSV | `/personas/exportar/csv` | GET | 
| 10 | % Activos | `/personas/analitica/activos-porcentaje` | GET | 
| 11 | Rangos Edad | `/personas/analitica/rangos-edad` | GET | 
| 12 | Top Dominios | `/personas/estadisticas/top-dominios` | GET | 
| 13 | Sin Notas | `/personas/analitica/sin-notas` | GET | 
| 14 | Rango Fechas | `/personas/fechas/rango/{inicio}/{fin}` | GET | 
| 15 | JSON | `/personas/exportar/json` | GET | 

---

## 📋 Requisitos

- Python 3.10+ (recomendado 3.11)

---

## 🚀 Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git https://github.com/lauratoro1/CRUD_FastAPI.git
cd CRUD_FastAPI
```

## Pruebas rápidas (curl extras)
```bash

# Reset - Eliminar todos los registros
curl -X DELETE http://127.0.0.1:8000/personas/reset

# Poblar - Carga masiva (500 registros)
curl -X POST "http://127.0.0.1:8000/personas/poblar" -H "Content-Type: application/json" -d '{"cantidad": 500}'

# Dominios - Estadísticas por dominio
curl http://127.0.0.1:8000/personas/estadisticas/dominios

# Edad - Estadísticas de edad
curl http://127.0.0.1:8000/personas/estadisticas/edad

# Buscar - Buscador general
curl http://127.0.0.1:8000/personas/buscar/juan

# Activos - Reporte de usuarios activos
curl http://127.0.0.1:8000/personas/reporte/activos

# Cumpleaños - Cumpleaños del mes (diciembre)
curl http://127.0.0.1:8000/personas/cumpleanios/mes/12

# Desactivar - Desactivación masiva
curl -X PATCH "http://127.0.0.1:8000/personas/bulk/desactivar" -H "Content-Type: application/json" -d '{"ids": [1,2,3]}'

# CSV - Exportar a CSV
curl http://127.0.0.1:8000/personas/exportar/csv -o datos.csv

# % Activos - Porcentaje de activos (Extra)
curl http://127.0.0.1:8000/personas/analitica/activos-porcentaje

# Rangos Edad - Rangos de edad (Extra)
curl http://127.0.0.1:8000/personas/analitica/rangos-edad

# Top Dominios - Top 5 dominios (Extra)
curl "http://127.0.0.1:8000/personas/estadisticas/top-dominios?limite=5"

# Sin Notas - Personas sin notas (Extra)
curl http://127.0.0.1:8000/personas/analitica/sin-notas

# Rango Fechas - Rango de fechas (Extra)
curl "http://127.0.0.1:8000/personas/fechas/rango/1990-01-01/2000-12-31"

# JSON - Exportar a JSON (Extra)
curl http://127.0.0.1:8000/personas/exportar/json -o datos.json

## Detener el servidor
# - Si lo iniciaste en la misma terminal: usa CTRL+C
# - Si corre en background: pkill -f uvicorn
