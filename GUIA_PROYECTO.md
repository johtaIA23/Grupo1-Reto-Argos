# Guía Completa — Sistema de Censo Digital de Ferreterías Colombia

## ¿Qué es este proyecto?

Sistema de inteligencia comercial para **Argos** que identifica, enriquece y gestiona ferreterías en Colombia como puntos de venta potenciales. Parte del programa **RTM (Road to Market)**.

**Flujo general:**
```
CSV con 130k empresas → Python API → Supabase (base de datos) → n8n (automatización) → Google Sheets + Dashboard
```

---

## Arquitectura del sistema

| Componente | Tecnología | Puerto | ¿Para qué? |
|---|---|---|---|
| **Python API** | FastAPI + pandas | 8000 | Procesa CSV, geocodifica, sirve el dashboard |
| **n8n** | n8n self-hosted | 5678 | Automatiza flujos: cargar CSV, exportar Sheets, chatbot IA |
| **Supabase** | PostgreSQL en la nube | — | Base de datos principal |
| **Dashboard RTM** | HTML estático | — | Panel de control visual |

---

## PASO A PASO — Poner el sistema a correr

### Requisitos previos

- **Docker Desktop** instalado y corriendo
- **Git** (opcional, para clonar)
- Carpeta del proyecto: `Avance Del Proyecto/`

---

### PASO 1 — Configurar las credenciales (.env)

El archivo `.env` ya existe en `Avance Del Proyecto/.env` con las credenciales reales del proyecto. No necesitas cambiarlo a menos que regeneres las claves.

**Variables incluidas:**
```
SUPABASE_URL=https://uhmdtvudfkehfhkkygkg.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  ← clave service_role de Supabase
OPENAI_API_KEY=sk-proj-...   ← para limpieza con IA
GROQ_API_KEY=gsk_...         ← para el chatbot
GOOGLE_MAPS_API_KEY=AIza...  ← para geocodificación
N8N_ENCRYPTION_KEY=cafe...   ← generada, no cambiar
```

> ⚠️ Si las claves expiran o necesitas nuevas, actualiza el archivo `.env` con los valores desde cada plataforma.

---

### PASO 2 — Verificar que el CSV está en su lugar

El CSV de ferreterías debe estar en:
```
Avance Del Proyecto/data/ferreterias.csv
```

Ya existe. Si lo reemplazas con uno nuevo, usa el mismo nombre de archivo.

---

### PASO 3 — Levantar los servicios con Docker

Abre una terminal **dentro de la carpeta `Avance Del Proyecto`**:

```bash
cd "c:\Users\Usuario\Documents\projects\Ferreterias Colombia\Avance Del Proyecto"
docker-compose up -d
```

Esto levanta:
- `python-api` en `http://localhost:8000`
- `n8n` en `http://localhost:5678`

**Para ver los logs en tiempo real:**
```bash
docker-compose logs -f
```

**Para detener todo:**
```bash
docker-compose down
```

**Para reconstruir la imagen de Python (si cambiaste el código):**
```bash
docker-compose build python-api
docker-compose up -d
```

> 💡 El código Python tiene **hot-reload**: los cambios en `python-api/app/` se aplican sin rebuild.

---

### PASO 4 — Verificar que todo está corriendo

| URL | ¿Qué muestra? |
|---|---|
| `http://localhost:8000/health` | Estado del API y CSV cargado |
| `http://localhost:8000/docs` | Swagger UI con todos los endpoints |
| `http://localhost:8000/rtm` | Dashboard RTM completo |
| `http://localhost:5678` | Panel de n8n |

---

### PASO 5 — Abrir el Dashboard RTM

El dashboard principal está en dos lugares:

1. **Desde el servidor:** `http://localhost:8000/rtm`
2. **Archivo directo:** `Dashboards/RTM_Road_To_Market.html` (abrirlo en el navegador)

> Si lo abres como archivo directo, las llamadas a la API usan `localhost:8000` — el servidor Python debe estar corriendo.

---

## Funciones del Dashboard — Guía de uso

### Panel de Procesos (pestaña principal)

#### 🔄 Cargar CSV a Supabase
Toma el archivo `data/ferreterias.csv` y lo sube a la base de datos. Usar cuando se tiene un CSV nuevo.

#### 📍 Geocodificar con Google Maps
Para cada ferretería sin coordenadas, busca la dirección en Google Maps y guarda `lat`, `lng`, `ciudad`, `departamento`, `telefono`, `website`. Consume cuota de Google Maps API.

#### 🔄 Migrar Base de Datos
Borra todo en Supabase y recarga desde el CSV. Usar cuando el CSV cambió completamente y quieres empezar de cero.

---

### Sección A — Limpieza IA

Detecta y elimina duplicados por NIT en Supabase.

1. Clic en **"Analizar"** → muestra cuántos registros tienen problemas
2. Clic en **"Ejecutar Limpieza"** → elimina duplicados, manteniendo el más reciente

---

### Sección B — Comparación de Archivos

Compara un CSV nuevo contra Supabase para identificar:
- **Nuevas** ferreterías (no están en Supabase)
- **Duplicadas exactas** (mismo NIT + misma fecha de matrícula)
- **Posibles duplicados** (mismo NIT pero diferente fecha, o nombre similar >80%)

**Cómo usar:**
1. Arrastra el CSV nuevo al área de carga
2. Espera el análisis
3. Revisa las pestañas: Nuevas / Duplicadas / Posibles
4. Descarga cada categoría como CSV si necesitas

---

### Sección C — Google Sheets Export

Exporta los datos de Supabase al Google Sheet de Argos.

1. **"Preparar con IA"** → detecta inconsistencias (nombres en minúscula, teléfonos mal formateados, NITs con caracteres extraños)
2. **"Exportar a Google Sheets"** → dispara el workflow de n8n que escribe en el Sheet

> El export usa el workflow `orquestador-proceso` de n8n. Asegúrate de que n8n esté corriendo en `localhost:5678`.

---

### Sección D — DatosColombia

Busca ferreterías en el registro público datos.gov.co (RUES) y las cruza contra Supabase.

1. **"Buscar Ahora"** → consulta los CIIUs 4663 y 4752
2. Resultado en las mismas 3 categorías que la Comparación
3. **Automatización** → actívala para que se ejecute cada 4 meses

---

### Chatbot flotante (burbuja azul, esquina inferior derecha)

Asistente IA conectado a n8n. Puede responder preguntas sobre los datos:
- "¿Cuántas ferreterías hay en Bogotá?"
- "¿Cuáles ferreterías no tienen teléfono?"
- "Muéstrame las de Medellín con probabilidad ALTA"

---

## Estructura de la base de datos (Supabase)

**Tabla: `ferreterias`**

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Clave primaria |
| `camara_comercio` | TEXT | Ciudad de la Cámara de Comercio |
| `razon_social` | TEXT | Nombre legal de la empresa |
| `nit` | TEXT | NIT (número de identificación tributaria) |
| `ciiu` | TEXT | Código CIIU (4663 o 4752) |
| `estado_matricula` | TEXT | ACTIVA / INACTIVA / etc. |
| `fecha_matricula` | DATE | Fecha de registro |
| `fecha_renovacion` | DATE | Última renovación |
| `representante_legal` | TEXT | Representante legal |
| `ciudad` | TEXT | Ciudad (llenada por Google Maps) |
| `departamento` | TEXT | Departamento |
| `telefono` | TEXT | Teléfono |
| `email` | TEXT | Email |
| `direccion` | TEXT | Dirección física |
| `lat` / `lng` | FLOAT | Coordenadas GPS |
| `probabilidad` | TEXT | ALTA / MEDIA / BAJA (potencial de venta Argos) |
| `num_fuentes` | INTEGER | Cuántas fuentes confirman el registro |
| `estado_info` | TEXT | Estado del enriquecimiento |
| `estado_legal` | TEXT | Estado legal |
| `website` | TEXT | Página web |
| `camara_comercio` | TEXT | Cámara de Comercio donde está registrada |
| `estado_matricula` | TEXT | Estado de la matrícula mercantil |

---

## Endpoints del Python API

Documentación interactiva completa en `http://localhost:8000/docs`

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio |
| GET | `/estadisticas` | Resumen del dataset |
| POST | `/procesar-csv` | Pagina registros del CSV |
| GET | `/consultar` | Búsqueda flexible |
| POST | `/reload-csv` | Recarga CSV sin reiniciar |
| POST | `/enriquecimiento/geocodificar` | Geocodifica con Google Maps |
| POST | `/enriquecimiento/migrar-supabase` | Migra CSV → Supabase |
| GET | `/limpieza/metricas` | Estadísticas de calidad |
| POST | `/limpieza/ejecutar` | Elimina duplicados |
| POST | `/comparar/subir` | Sube CSV para comparar |
| POST | `/comparar/exportar/{categoria}` | Descarga resultados |
| GET | `/sheets/metricas` | Métricas para export |
| POST | `/sheets/exportar` | Trigger n8n export |
| POST | `/datoscolombia/buscar` | Busca en datos.gov.co |
| GET | `/rtm` | Dashboard RTM HTML |

---

## Workflows de n8n

Accede en `http://localhost:5678`

| Workflow | Descripción |
|---|---|
| `00_orquestador` | Router principal — recibe todos los mensajes del chatbot y los dirige |
| `orquestador-proceso` | Ejecuta procesos: exportar Sheets, etc. |
| `05_sub_carga_csv` | Carga el CSV a Supabase |
| `06_sub_enriquecimiento_maps` | Enriquece con Google Maps |
| `07_sub_exportar_sheets` | Escribe en Google Sheets |
| `04_sub_agente_ia` | Responde preguntas con IA sobre los datos |
| `08 - Sub_ Web Scraping Portafolio` | Scraping de portafolio web |

---

## Solución de problemas comunes

### "No se puede conectar a localhost:8000"
```bash
docker-compose ps          # ¿está corriendo python-api?
docker-compose logs python-api  # ver error
```

### "Error al cargar CSV"
- Verificar que `data/ferreterias.csv` existe
- El CSV debe tener encoding UTF-8
- La primera fila debe ser el encabezado

### "Error de Supabase 401/403"
- La `SUPABASE_SERVICE_KEY` venció o es incorrecta
- Ir a Supabase → Settings → API → Regenerar service_role key
- Actualizar `.env` y reiniciar: `docker-compose restart python-api`

### "n8n no exporta a Sheets"
1. Verificar que n8n está en `localhost:5678`
2. En n8n, verificar que el workflow `orquestador-proceso` está **activo** (toggle verde)
3. Verificar que las credenciales de Google Sheets en n8n no vencieron

### Reconstruir después de cambios en código Python
```bash
docker-compose build python-api
docker-compose up -d
```

### Ver logs en vivo
```bash
docker-compose logs -f python-api   # solo el API
docker-compose logs -f n8n          # solo n8n
docker-compose logs -f              # todo
```

---

## Archivos importantes del proyecto

```
Ferreterias Colombia/
├── Avance Del Proyecto/
│   ├── docker-compose.yml          ← configuración de Docker
│   ├── .env                        ← credenciales (NO compartir)
│   ├── .env.example                ← plantilla sin credenciales
│   ├── data/
│   │   └── ferreterias.csv         ← CSV fuente (130k empresas)
│   ├── python-api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py             ← punto de entrada del API
│   │       ├── config.py           ← variables de entorno
│   │       └── routers/
│   │           ├── csv_processor.py    ← carga y procesa CSV
│   │           ├── enriquecimiento.py  ← Google Maps + Supabase
│   │           ├── limpieza_ia.py      ← detecta/elimina duplicados
│   │           ├── comparar_archivo.py ← compara CSVs
│   │           ├── sheets_export.py    ← prepara export Sheets
│   │           ├── datos_colombia.py   ← busca en datos.gov.co
│   │           ├── dashboard.py        ← sirve el HTML del dashboard
│   │           └── estadisticas.py     ← resumen del dataset
│   ├── n8n/                        ← JSONs de los workflows
│   ├── n8n_data/                   ← datos persistentes de n8n (NO borrar)
│   └── supabase/                   ← scripts SQL para crear tablas
└── Dashboards/
    └── RTM_Road_To_Market.html     ← dashboard principal
```

---

## Comandos de referencia rápida

```bash
# Levantar todo
cd "Avance Del Proyecto"
docker-compose up -d

# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Rebuild (si cambias Dockerfile o requirements.txt)
docker-compose build python-api && docker-compose up -d

# Recargar CSV sin reiniciar
curl -X POST http://localhost:8000/reload-csv
```
