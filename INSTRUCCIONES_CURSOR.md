# Instrucciones para Claude Code en Cursor
## Proyecto: Extractor de Facturas de Vehículos

## Contexto del Proyecto

Aplicación web para concesionarias de autos que automatiza la extracción de datos de facturas PDF de terminales de vehículos. Las operadoras actualmente extraen estos datos manualmente. La app debe permitir subir PDFs en lote, extraer datos automáticamente, editarlos si es necesario, y exportar a Excel.

**Carpeta del proyecto**: `c:\Users\Marlen Virga\Desktop\gabi actis`

## Stack Tecnológico

- **Frontend**: React + Vite (JavaScript)
- **Styling**: CSS Vanilla con variables CSS, tema oscuro, diseño moderno premium
- **Backend**: Python 3.12 + Flask
- **PDF**: PyPDF2 (los PDFs son digitales con texto seleccionable)
- **Excel**: openpyxl (lectura de planillas de búsqueda + escritura del Excel final)
- **Base de datos**: SQLite (built-in de Python)
- **CORS**: flask-cors

## Estructura del Proyecto

```
gabi-actis/
├── client/                          # Frontend React + Vite
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx       # Drag & drop de PDFs
│   │   │   ├── DataTable.jsx        # Tabla editable de resultados
│   │   │   ├── ExportButton.jsx     # Exportación a Excel
│   │   │   ├── LookupManager.jsx    # Gestión de planillas
│   │   │   ├── ProgressBar.jsx
│   │   │   ├── Header.jsx
│   │   │   └── StatusBadge.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── styles/
│   │   │   └── index.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── server/                          # Backend Python + Flask
│   ├── app.py                       # Entry point Flask
│   ├── requirements.txt
│   ├── routes/
│   │   ├── upload.py
│   │   ├── extractions.py
│   │   ├── export.py
│   │   └── lookup_tables.py
│   ├── services/
│   │   ├── pdf_parser.py
│   │   ├── brand_detector.py
│   │   ├── data_extractor.py
│   │   ├── lookup_service.py
│   │   └── excel_generator.py
│   ├── extractors/
│   │   ├── base_extractor.py
│   │   ├── byd_extractor.py
│   │   ├── nissan_extractor.py
│   │   ├── inchcape_extractor.py    # Subaru + Suzuki (mismo formato)
│   │   ├── kia_extractor.py
│   │   ├── honda_extractor.py
│   │   └── __init__.py
│   ├── models/
│   │   └── database.py
│   ├── uploads/
│   └── lookup_tables/
│
└── README.md
```

## Base de Datos SQLite

```sql
CREATE TABLE extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    brand TEXT,
    model_code TEXT,
    model_name TEXT,
    vin TEXT,
    interno TEXT,
    engine_number TEXT,
    is_hybrid BOOLEAN DEFAULT FALSE,
    is_electric BOOLEAN DEFAULT FALSE,
    color_name TEXT,
    color_code TEXT,
    raw_text TEXT,
    confidence TEXT DEFAULT 'high',
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE color_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    color_name TEXT NOT NULL,
    color_code TEXT NOT NULL
);

CREATE TABLE model_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    model_name TEXT NOT NULL,
    model_code TEXT NOT NULL
);
```

## API REST

| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/upload | Sube PDFs y extrae datos automáticamente |
| GET | /api/extractions | Lista todas las extracciones |
| GET | /api/extractions/:id | Detalle de una extracción |
| PUT | /api/extractions/:id | Actualiza datos (edición manual) |
| DELETE | /api/extractions/:id | Elimina una extracción |
| POST | /api/export | Genera Excel con las extracciones seleccionadas |
| POST | /api/lookup-tables/colors | Sube planilla de colores |
| POST | /api/lookup-tables/models | Sube planilla de modelos |
| GET | /api/lookup-tables/colors | Lista colores cargados |
| GET | /api/lookup-tables/models | Lista modelos cargados |

## Excel de Salida (5 columnas)

| # | Columna | Descripción |
|---|---|---|
| 1 | INTERNO | Últimos 8 caracteres del VIN |
| 2 | MODELO | Código del modelo si existe, sino nombre del modelo |
| 3 | Nº DE VIN | VIN completo (17 caracteres) |
| 4 | Nº DE MOTOR | Motor naftero (o eléctrico si solo eléctrico) |
| 5 | CÓDIGO DE COLOR | Código buscado en planilla |

## Lógica del Nro Motor

Siempre se extrae UN solo número de motor:
- Vehículo solo nafta → su único motor
- Vehículo híbrido (nafta + eléctrico) → el motor NAFTERO
- Vehículo solo eléctrico → el motor ELÉCTRICO (es el único que tiene)

## Lógica del campo MODELO

- Si la factura trae código de modelo → usar el código
- Si NO trae código → poner el nombre del modelo (para buscar código en planilla maestra a futuro)

## 6 Marcas — Detección y Extracción

### 1. BYD (🔴 Alta complejidad) — Detectar: "BYD AUTO ARGENTINA" en texto

El texto del PDF viene desordenado y concatenado. Emisor: BYD AUTO ARGENTINA S.A.U.

Texto ejemplo:
```
SHARKDMO-GSLPE19W2A9TF162659TZ220XYV4R6003827/
TZ200XSV2H60BYD BYD476ZQFT26000079
BlackPallas WhiteLPE19W2A9TF162659BYD
17982310-0011
```
Factura visual: Codigo = `17982310-00`, Descripción = `BYD SHARK DMO GS PALLAS WHITE BLACK`

| Campo | Patrón |
|---|---|
| Código modelo | `\d{8}-\d{2}` (ej: `17982310-00`) |
| VIN | `[L][A-Z0-9]{16}` (17 chars empezando con L) |
| Motor naftero | `BYD\d{3}[A-Z]{2}\S+` (ej: `BYD476ZQFT26000079`) |
| Motor eléctrico | `TZ\d{3}X\S+` (findall, para detectar tipo) |
| Color | Buscar nombres de la planilla BYD en el texto |
| Nombre modelo | Extraer de descripción (ej: `SHARK DMO GS`) |
| Planilla colores | `codigos de colores byd.xlsx` — combinar EXT/INT |

Color BYD: viene separado (exterior + interior). Concatenar como `EXTERIOR/INTERIOR` en MAYÚSCULAS para buscar en planilla.
Ej: Ext=`Pallas White`, Int=`Black` → buscar `PALLAS WHITE/BLACK` → código `PLWB`

### 2. Nissan (🟡 Media) — Detectar: "NISSAN ARGENTINA S.A." en texto

Emisor: NISSAN ARGENTINA S.A. Campos etiquetados pero concatenados en última línea.

Texto ejemplo:
```
MOTOR NRO: HR16474380P
TIPO: SEDAN 5 PUERTASMODELO: KAIT 1.6 EXCLUSIVE CVT
NRO DESPACHO: 26008IG04003613TCERTIFICADO: 08-0160907/2026CHASIS MARCA: NISSANCOLOR: Metálico Platino LíquidoVIN: 94DFCAP15VB100787PESO: 1.167
```

| Campo | Patrón |
|---|---|
| VIN | `VIN:\s*([A-Z0-9]{17})` |
| Motor | `MOTOR NRO:\s*(\S+)` |
| Color | `COLOR:\s*(.+?)(?=VIN:)` |
| Modelo (nombre) | `MODELO:\s*(.+?)(?=\d+\s*C/U)` |
| Código modelo | No tiene → usar nombre del modelo |
| Planilla colores | `CODIGOS COLORES AUTOPAK.xlsx` |

3 páginas (Original, Duplicado, Triplicado) con mismo contenido. Solo leer página 1.

### 3. Subaru y Suzuki — INCHCAPE (🟢 Fácil) — Detectar: "Marca: Subaru" o "Marca: Suzuki"

Emisor: INCHCAPE ARGENTINA S.A. (Subaru) / DISTRIBUIDORA AUTOMOTRIZ ARGENTINA S.A. (Suzuki)
MISMO formato para ambas marcas.

Texto ejemplo:
```
1Marca: Subaru
Modelo: ARCRTK02
Chasis: JF2GU45M1TG089659
Motor: ZE05654
Color: AZUL ZAFIRO PERLADO
Modelo Comercial: CROSSTREK 2.0I
AWD CVT LIMITED ESARCRTK02 30.557,85 % 0.00 30.557,85
```

| Campo | Patrón |
|---|---|
| Código modelo | `Modelo:\s*(\S+)` (ya viene el código: ARCRTK02, ARSW0005) |
| Nombre modelo | `Modelo Comercial:\s*(.+)` + siguiente línea |
| VIN | `Chasis:\s*(\S+)` |
| Motor | `Motor:\s*(\S+)` |
| Color | `Color:\s*(.+)` |
| Planilla colores | `CODIGOS COLORES AUTOPAK.xlsx` |

2 páginas (Original, Duplicado). Solo leer página 1.

### 4. KIA (🟡 Media) — Detectar: "MARCAMOTOR: KIA" o "MARCA:KIA"

Emisor: KIA ARGENTINA. Campos etiquetados pero muy concatenados.

Texto ejemplo:
```
MODELO: COLOR:BLANCO CLARO
TIPO:CODIGO DEMODELO: HDH46B857DDPKHUDGW
MARCAMOTOR: KIA
MARCACHASIS: KIA NUMERO DEMOTOR: D4CBTD618781
NUMERO DECHASIS: KNCSJX76AT7918387NUMERO DECERTIFICADO: 008-0126191/2026AÑO:2026UNAUNIDAD0KMMARCA:KIA
K2500
```

| Campo | Patrón |
|---|---|
| Código modelo | `CODIGO DEMODELO:\s*(\S+)` |
| Nombre modelo | Línea suelta después de datos del chasis (ej: `K2500`) |
| VIN | `NUMERO DECHASIS:\s*([A-Z0-9]{17})` |
| Motor | `NUMERO DEMOTOR:\s*(\S+)` |
| Color | `COLOR:(.+?)$` (en la línea que tiene MODELO:) |
| Planilla colores | `CODIGOS COLORES AUTOPAK.xlsx` |

3 páginas (Original, Duplicado, Triplicado). Solo leer página 1.

### 5. Honda (🟢 Fácil) — Detectar: "Marca: HONDA" en texto

Emisor: Honda Motor de Argentina S.A. Campos etiquetados claros, uno por línea.

Texto ejemplo:
```
    Modelo: HR-V RV3 3    Equipo Nro:
    Artículo: 3M7XKJ7-KK-N28
    Descripción: HR-V RV3 3M7 EXL
    Marca: HONDA
    Color: URBAN GRAY P.
    Nro Motor: L15ZJ6604506
    Nro Chasis: 93HRV3860TK304199
    Despacho Nro: 26-008-IG04-002595 E
```

| Campo | Patrón |
|---|---|
| Código modelo | No tiene código explícito (Artículo podría servir a futuro) |
| Nombre modelo | `Descripci.n:\s*(.+)` o `Modelo:\s*(.+?)(?:\s{2,}|$)` |
| VIN | `Nro Chasis:\s*(\S+)` |
| Motor | `Nro Motor:\s*(\S+)` |
| Color | `Color:\s*(.+)` |
| Planilla colores | `CODIGOS COLORES AUTOPAK.xlsx` |

1 sola página.

## Planillas de Búsqueda Existentes (ya en la carpeta del proyecto)

1. **`codigos de colores byd.xlsx`** — 28 colores BYD
   - Columnas: Código | Descripción
   - Ej: `PLWB` → `PALLAS WHITE/BLACK`

2. **`CODIGOS COLORES AUTOPAK.xlsx`** — ~499 colores multi-marca (Nissan, Subaru, Suzuki, KIA, Honda)
   - Columnas: Código | Descripción | Fecha Baja
   - Los datos empiezan en fila 5 (las primeras 4 son encabezados)

## Funcionalidades del MVP

1. **Carga en lote**: Drag & drop o selector para múltiples PDFs
2. **Extracción automática**: Detectar marca → ejecutar extractor → buscar códigos en planillas
3. **Revisión y edición**: Tabla editable, campos resaltados si no se pudo extraer
4. **Exportación a Excel**: 5 columnas (INTERNO, MODELO, VIN, MOTOR, CÓDIGO COLOR)
5. **Gestión de planillas**: Subir/actualizar planillas de códigos

## Notas de Implementación

- El frontend debe tener diseño moderno, premium, con tema oscuro, animaciones suaves
- Los PDFs de las facturas de ejemplo están en la misma carpeta del proyecto para testing
- El INTERNO se calcula: últimos 8 caracteres del VIN
- La máquina NO tiene Node.js instalado (hay que instalarlo primero)
- La máquina SÍ tiene Python 3.12, Git, y Docker Desktop
- La app se despliega en un servidor interno de la empresa (red local)
- No requiere autenticación

## Git / GitHub

### Estrategia de Ramas (Simple: main + develop)

| Rama | Propósito |
|---|---|
| `main` | Código estable, producción. Solo recibe merges de `develop` |
| `develop` | Rama de desarrollo activa |
| `feature/*` | Ramas por funcionalidad, se crean desde `develop` |

### Workflow por Fase
1. Crear repo en GitHub + `git init` + `.gitignore` + primer commit en `main`
2. Crear rama `develop` desde `main`
3. Para cada fase crear `feature/nombre` desde `develop`
4. Al terminar feature, merge a `develop`
5. Al final, merge `develop` → `main`

### `.gitignore`
```
__pycache__/
*.pyc
venv/
.env
node_modules/
dist/
*.db
server/uploads/*
!server/uploads/.gitkeep
.vscode/
.idea/
.DS_Store
Thumbs.db
*.log
```

## Docker

Docker se usa tanto para desarrollo como para producción en el servidor interno.

### `Dockerfile.backend`
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ .
EXPOSE 5000
CMD ["python", "app.py"]
```

### `Dockerfile.frontend`
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY client/package*.json ./
RUN npm install
COPY client/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### `docker-compose.yml`
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5000:5000"
    volumes:
      - ./server:/app
      - sqlite_data:/app/data
      - ./server/uploads:/app/uploads
      - ./server/lookup_tables:/app/lookup_tables
    environment:
      - FLASK_ENV=development
      - DATABASE_PATH=/app/data/app.db
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
volumes:
  sqlite_data:
```

### `nginx.conf`
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

### `.dockerignore`
```
node_modules/
venv/
__pycache__/
*.pyc
.git/
*.db
.env
```

### Comandos Docker
- `docker-compose up --build` — Construir y levantar
- `docker-compose up -d` — Background
- `docker-compose down` — Detener
- `docker-compose logs -f backend` — Ver logs
