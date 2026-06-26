# Lector de Facturas de Vehículos · Neostar I+D

Aplicación web para concesionarias que automatiza la extracción de datos de
facturas PDF de las terminales de vehículos. Permite subir PDFs en lote, extraer
los datos automáticamente, revisarlos/editarlos y exportarlos a Excel.

## Stack

- **Frontend**: React + Vite (JavaScript), CSS vanilla (estética Neostar, tema claro)
- **Backend**: Python 3.12 + Flask, PyPDF2, openpyxl
- **Base de datos**: SQLite
- **Despliegue**: Docker (backend Flask + frontend Nginx)

## Marcas soportadas

BYD · Nissan · Subaru · Suzuki · KIA · Honda

Cada marca tiene su propio extractor (`server/extractors/`). La marca se detecta
automáticamente desde el texto de la factura.

## Lógica de negocio

- **INTERNO**: últimos 8 caracteres del VIN.
- **MODELO**: código del modelo si la factura lo trae; si no, el nombre del modelo.
- **Nº DE MOTOR**: el motor naftero en híbridos; el eléctrico si el vehículo es solo eléctrico.
- **CÓDIGO DE COLOR**: se resuelve contra las planillas de colores
  (BYD usa su propia planilla; el resto, la planilla AUTOPAK).

## Estructura

```
client/   Frontend React + Vite
server/   Backend Flask (routes, services, extractors, models)
Dockerfile.backend / Dockerfile.frontend / docker-compose.yml / nginx.conf
```

## Desarrollo con Docker (recomendado)

Requiere Docker Desktop corriendo.

```bash
docker-compose up --build      # construir y levantar
docker-compose up -d           # en segundo plano
docker-compose down            # detener
docker-compose logs -f backend # ver logs del backend
```

- Frontend: http://localhost (puerto 80)
- Backend API: http://localhost:5000/api

## Desarrollo local (sin Docker)

**Backend** (requiere Python 3.12):

```bash
cd server
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
python app.py                 # http://localhost:5000
```

**Frontend** (requiere Node.js 20+ — no viene instalado en la máquina):

```bash
cd client
npm install
npm run dev                   # http://localhost:5173 (proxy /api -> :5000)
```

## API REST

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/upload` | Sube PDFs y extrae datos |
| GET | `/api/extractions` | Lista extracciones |
| GET | `/api/extractions/:id` | Detalle |
| PUT | `/api/extractions/:id` | Edición manual (recalcula interno al editar VIN) |
| DELETE | `/api/extractions/:id` | Elimina |
| POST | `/api/export` | Genera Excel (5 columnas) |
| GET/POST | `/api/lookup-tables/colors` | Lista/sube planilla de colores |
| GET/POST | `/api/lookup-tables/models` | Lista/sube planilla de modelos |

## Excel de salida

`INTERNO · MODELO · Nº DE VIN · Nº DE MOTOR · CÓDIGO DE COLOR`

## Notas

- Las planillas de colores semilla viven en `server/lookup_tables/` y se cargan
  automáticamente al primer arranque.
- Las facturas escaneadas (sin capa de texto) se marcan con confianza baja y
  estado "revisar" para edición manual.
- La app no requiere autenticación (uso en red interna).

## Git

Ramas: `main` (estable) ← `develop` ← `feature/*` (una por fase).
