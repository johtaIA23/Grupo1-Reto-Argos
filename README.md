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

# Manual uso dashboard
# 📊 Manual de Usuario — RTM_Road_To_Market
### Inteligencia Comercial · Materiales de Construcción

> **Versión:** 3.0 · **Archivo:** `RTM_Road_To_Market.html` · **Idioma:** Español colombiano

---

## Tabla de Contenidos

1. [¿Qué es este dashboard?](#1-qué-es-este-dashboard)
2. [Requisitos técnicos](#2-requisitos-técnicos)
3. [Cómo abrir el dashboard](#3-cómo-abrir-el-dashboard)
4. [Cargar o actualizar la base de datos](#4-cargar-o-actualizar-la-base-de-datos)
5. [Indicadores Clave — KPIs](#5-indicadores-clave--kpis)
6. [Filtros de búsqueda](#6-filtros-de-búsqueda)
7. [Mapa de Territorios Prioritarios](#7-mapa-de-territorios-prioritarios)
8. [Ranking de ciudades](#8-ranking-de-ciudades)
9. [Análisis Multidimensional — Gráficas](#9-análisis-multidimensional--gráficas)
10. [Directorio de Empresas — Tabla](#10-directorio-de-empresas--tabla)
11. [Exportar resultados](#11-exportar-resultados)
12. [El Score de Prioridad — cómo se calcula](#12-el-score-de-prioridad--cómo-se-calcula)
13. [Estructura requerida del archivo Excel](#13-estructura-requerida-del-archivo-excel)
14. [Preguntas frecuentes](#14-preguntas-frecuentes)
15. [Glosario de términos](#15-glosario-de-términos)

---

## 1. ¿Qué es este dashboard?

El **Dashboard RTM_Road_To_Market** es una herramienta de inteligencia comercial diseñada para apoyar la **toma de decisiones sobre el despliegue de la fuerza de ventas de cemento** en territorios donde la empresa aún no tiene presencia consolidada.

Permite responder preguntas estratégicas como:

- ¿En qué ciudades hay más ferreterías y distribuidores con alta probabilidad de compra?
- ¿Qué departamentos presentan el mayor score de oportunidad comercial?
- ¿Qué empresas están próximas a renovar su matrícula y representan un contacto urgente?
- ¿Dónde están ubicadas exactamente esas empresas y cuál es su dirección?
- ¿Cuántos clientes potenciales activos hay por territorio?

El dashboard procesa el archivo Excel de la base de datos, calcula automáticamente un **Score de Prioridad** por empresa y presenta toda la información en un mapa interactivo con etiquetas por empresa, ranking de ciudades, gráficas de análisis y una tabla del directorio completo — todo desde un solo archivo `.html`, sin instalaciones adicionales.

---

## 2. Requisitos técnicos

| Elemento | Detalle |
|---|---|
| **Navegador web** | Google Chrome, Microsoft Edge o Mozilla Firefox (versión reciente) |
| **Conexión a internet** | Requerida únicamente para visualizar el mapa base (cartografía) |
| **Archivo de datos** | Excel en formato `.xlsx` o `.xls` con la estructura definida en la [Sección 13](#13-estructura-requerida-del-archivo-excel) |
| **Instalaciones adicionales** | Ninguna — el dashboard es completamente autónomo |

> ⚠️ **No use Internet Explorer.** Use Chrome o Edge para garantizar el funcionamiento correcto de todas las funciones del tablero.

---

## 3. Cómo abrir el dashboard

1. Localice el archivo `RTM_Road_To_Market.html` en su computador.
2. Haga **doble clic** — se abrirá automáticamente en su navegador predeterminado.
3. Verá la pantalla de bienvenida con el mensaje *"Cargue su base de datos para iniciar"*.
4. Desde allí puede cargar su archivo Excel o explorar el tablero haciendo clic en **"Cargar datos de muestra"**.

```
📁 RTM_Road_To_Market.html  ←  Doble clic para abrir
```

---

## 4. Cargar o actualizar la base de datos

### Cargar un archivo nuevo

**Paso 1 —** Haga clic en el botón **`Cargar / Actualizar Excel`** en la esquina superior derecha del encabezado (barra azul oscura).

**Paso 2 —** Se abrirá el explorador de archivos. Navegue hasta donde está guardado su archivo Excel y selecciónelo.

**Paso 3 —** Aparecerá brevemente un indicador de carga animado mientras el tablero procesa los registros.

**Paso 4 —** Al finalizar, todos los KPIs, el mapa, las gráficas, el ranking y la tabla se actualizarán automáticamente.

### Actualizar con datos más recientes

Haga clic nuevamente en **`Cargar / Actualizar Excel`** y seleccione el nuevo archivo. Los datos anteriores se reemplazarán en su totalidad.

### Usar los datos de muestra

En la pantalla de bienvenida, haga clic en **"Cargar datos de muestra"** para explorar todas las funciones del tablero con 10 registros reales de ferreterías en distintas ciudades de Colombia.

> 💡 El número total de registros cargados se muestra en la esquina superior derecha del encabezado, en color amarillo-verde, junto al texto **"Empresas cargadas"**.

---

## 5. Indicadores Clave — KPIs

Al cargar los datos, aparecen **6 tarjetas de KPIs** en la parte superior del tablero. Todos se actualizan en tiempo real al aplicar cualquier filtro.

| # | Tarjeta | Qué mide | Para qué sirve |
|---|---|---|---|
| 1 | 🏢 **Total Empresas** | Total de registros con los filtros actuales | Dimensionar el universo de clientes potenciales del territorio |
| 2 | ✅ **Matrículas Activas** | Cantidad y porcentaje con estado `ACTIVA` | Identificar qué proporción del mercado está legalmente operativa |
| 3 | 🎯 **Prioridad Alta (A)** | Empresas con Score ≥ 70 puntos | **Lista crítica de contacto inmediato** — el KPI más estratégico del tablero |
| 4 | 📈 **Score Promedio** | Promedio del Score del segmento filtrado | Medir el atractivo comercial general de una zona o región |
| 5 | 🔔 **Renovación ≤ 90 días** | Matrículas que vencen en los próximos 90 días | Ventana urgente — son empresas en proceso de revisión de proveedores |
| 6 | 📅 **Renovación ≤ 365 días** | Empresas en el pipeline del año calendario | Planificación del calendario de visitas anuales |

> 🎯 La tarjeta **Prioridad Alta (A)** se resalta con borde superior amarillo-verde y lleva la etiqueta **CRÍTICO** — es el indicador de mayor valor estratégico para priorizar visitas comerciales.

---

## 6. Filtros de búsqueda

La barra de filtros permite segmentar los datos para enfocarse en territorios o segmentos específicos. **Todo el tablero** (KPIs, mapa, ranking, gráficas y tabla) se actualiza instantáneamente al cambiar cualquier filtro.

### Filtros disponibles

| Filtro | Función | Comportamiento especial |
|---|---|---|
| **Departamento** | Muestra solo empresas del departamento seleccionado | Al cambiar el departamento, el filtro **Ciudad se actualiza automáticamente** mostrando solo las ciudades de ese departamento |
| **Ciudad** | Filtra por municipio específico | Depende del departamento activo. Sin departamento seleccionado, muestra todas las ciudades |
| **Cámara de Comercio** | Segmenta por la cámara de comercio de origen | Independiente de los demás filtros |
| **Estado Matrícula** | Filtra por `ACTIVA`, `INACTIVA` o `CANCELADA` | — |
| **Prioridad Score** | Muestra solo la categoría elegida: A, B o C | — |
| **Buscar Razón Social / NIT** | Búsqueda libre por nombre de empresa o NIT | Filtra en tiempo real mientras escribe |

### Filtro encadenado Departamento → Ciudad

Al seleccionar un **Departamento**, el desplegable de **Ciudad** se repuebla mostrando únicamente las ciudades con empresas en ese departamento. Si luego cambia de departamento y la ciudad anterior no corresponde al nuevo, el campo Ciudad se limpia automáticamente. Al hacer clic en **`✕ Limpiar`**, se restauran todas las ciudades disponibles.

### Botones de acción

| Botón | Función |
|---|---|
| **`✕ Limpiar`** | Restablece todos los filtros y muestra el universo completo |
| **`⬇ Exportar`** | Descarga en Excel los registros actualmente filtrados |

### Ejemplo de uso estratégico

> *Necesito la lista de ferreterías activas de alta prioridad en Antioquia para asignar rutas esta semana.*
>
> 1. Seleccione **Departamento → Antioquia** *(las ciudades se actualizan automáticamente)*
> 2. Seleccione **Estado Matrícula → ACTIVA**
> 3. Seleccione **Prioridad Score → A — Alta (≥70)**
> 4. Haga clic en **`⬇ Exportar`** para generar el listado de trabajo

---

## 7. Mapa de Territorios Prioritarios

El mapa muestra geográficamente la distribución de empresas en Colombia con **dos capas de interacción** que se actualizan con cada filtro aplicado.

### Capa 1 — Burbujas de ciudad

Círculos agrupados por ciudad que ofrecen una vista general del territorio.

**Color — indica el Score promedio de la ciudad:**

| Color | Score promedio | Significado operativo |
|---|---|---|
| 🟡 **Amarillo-verde** | ≥ 70 puntos | Prioridad Alta — acción inmediata |
| 🟠 **Naranja** | 40 a 69 puntos | Prioridad Media — planificar este mes |
| 🔴 **Rojo** | < 40 puntos | Prioridad Baja — seguimiento trimestral |

**Tamaño — proporcional** al número de empresas en esa ciudad. A mayor burbuja, mayor concentración de clientes potenciales.

**Al hacer clic en una burbuja** se abre un panel con:
- Nombre de ciudad y departamento
- Total de empresas y desglose por prioridad (A / B / C)
- Score promedio de la ciudad
- **Listado completo de todas las empresas** de esa ciudad con su score individual y dirección, en un panel con desplazamiento vertical

### Capa 2 — Puntos individuales por empresa

Cada empresa con coordenadas geográficas tiene su propio punto en el mapa, con el mismo código de color del score.

**Al pasar el mouse por encima de un punto** aparece un **tooltip flotante compacto** con:
- Nombre de la empresa (truncado con `…` si es largo)
- Dirección del establecimiento

El tooltip desaparece automáticamente al mover el mouse.

**Al hacer clic en el punto** se abre una **ficha detallada** con:
- Nombre completo de la empresa
- Ciudad y departamento
- Dirección completa
- NIT, estado de matrícula, antigüedad y teléfono
- Score y categoría de prioridad

### Controles de navegación del mapa

| Acción | Resultado |
|---|---|
| **Rueda del mouse** | Zoom de acercamiento o alejamiento |
| **Clic + arrastrar** | Desplazamiento por el mapa |
| **Botones `+` / `−`** | Zoom controlado (esquina superior izquierda) |

### Indicador de cobertura

En la esquina superior derecha del mapa aparece el contador actualizado con el formato:

```
X ciudades · Y empresas
```

Refleja exactamente cuántas ciudades y empresas tienen coordenadas y están visibles con los filtros activos.

> ℹ️ Solo aparecen en el mapa las empresas que tienen coordenadas geográficas válidas (`lat` y `lng`) dentro del rango de Colombia. Las que no tienen coordenadas aparecen correctamente en la tabla y en los KPIs.

> 🌐 El mapa requiere conexión a internet para cargar el fondo cartográfico (OpenStreetMap / CARTO). Sin internet, el resto del tablero funciona con normalidad.

---

## 8. Ranking de ciudades

El panel lateral derecho muestra el **Top 15 de ciudades** ordenadas por Score promedio descendente, actualizadas con los filtros activos.

### Cómo leer el ranking

| Elemento | Significado |
|---|---|
| **Número de posición** | Lugar en el ranking (1 = mayor Score promedio) |
| **Fondo dorado** | Posiciones 1, 2 y 3 — territorios de máxima oportunidad |
| **Nombre y línea inferior** | Ciudad con departamento y cantidad de empresas registradas |
| **Número a la derecha** | Score promedio de todas las empresas de esa ciudad |
| **Barra horizontal** | Representa visualmente el score relativo al líder del ranking |

> Las ciudades en las primeras posiciones del ranking son las que deben recibir **visita o contacto prioritario** en el período inmediato.

---

## 9. Análisis Multidimensional — Gráficas

Esta sección presenta **dos gráficas** que se actualizan con cada filtro, diseñadas para apoyar decisiones de asignación de recursos comerciales.

---

### 📊 Gráfica 1 — Score Promedio por Departamento

**Tipo:** Barras horizontales ordenadas de mayor a menor (Top 8 departamentos)

Cada barra representa el Score promedio de todas las empresas registradas en ese departamento. El valor numérico aparece al final de cada barra.

**Interpretación:** Los departamentos con barras más largas ofrecen el mayor retorno esperado por visita comercial y deben recibir recursos de ventas en primer lugar.

---

### 🎯 Gráfica 2 — Distribución por Prioridad

**Tipo:** Barras de progreso por categoría con porcentaje

Muestra cuántas empresas hay en cada nivel de prioridad y qué porcentaje representan sobre el total filtrado.

| Categoría | Color | Criterio | Acción |
|---|---|---|---|
| **A** | 🟡 Amarillo-verde | Score ≥ 70 | Contacto esta semana |
| **B** | 🟠 Naranja | Score 40 a 69 | Planificar en el mes |
| **C** | 🔴 Rojo | Score < 40 | Seguimiento trimestral |

**Interpretación:** Permite dimensionar la carga de trabajo del equipo de ventas y distribuir los recursos según la densidad de oportunidades por categoría en cada territorio.

---

## 10. Directorio de Empresas — Tabla

La tabla muestra el directorio completo de empresas del territorio filtrado con toda la información necesaria para la gestión comercial directa.

### Columnas de la tabla

| Columna | Descripción | Indicadores visuales |
|---|---|---|
| **Score** | Puntaje calculado automáticamente (0–100) | 🟢 Verde ≥70 · 🟡 Amarillo 40–69 · 🔴 Rojo <40 |
| **Prio.** | Categoría de prioridad asignada | ● A verde · ● B naranja · ● C rojo |
| **Razón Social** | Nombre legal de la empresa | Truncado con tooltip al pasar el cursor |
| **NIT** | Número de identificación tributaria | — |
| **Ciudad** | Municipio de registro | — |
| **Departamento** | Departamento de registro | — |
| **Cámara Comercio** | Cámara que expidió la matrícula | Truncado con tooltip |
| **Estado** | Estado de la matrícula mercantil | 🟢 ACTIVA · 🔴 INACTIVA · 🟡 Otros |
| **Antigüedad** | Años desde la fecha de matrícula inicial | Con un decimal (ej: `12.3 años`) |
| **Fuentes** | Fuentes de información verificadas | Valor numérico (0 a 3) |
| **Renovación** | Fecha de vencimiento de la matrícula | Formato DD/MM/AAAA |
| **Representante** | Nombre del representante legal | Truncado con tooltip |
| **Dirección** | Dirección completa del establecimiento | En gris, truncado con tooltip |

### Ordenar la tabla

Haga clic en el **encabezado de cualquier columna** para ordenar por ese campo en orden descendente. Un segundo clic invierte el orden (ascendente ↔ descendente). La columna activa se resalta en color amarillo-verde con una flecha indicadora `↑ ↓`.

> 💡 **Tip:** Ordene por **Score descendente** para tener las empresas de mayor potencial al tope — esas son las primeras visitas a asignar al equipo de campo.

### Paginación

La tabla muestra **20 registros por página**. Use los controles `‹ 1 2 3 … ›` en la parte inferior derecha para navegar. El contador inferior izquierdo indica el rango visible y el total de registros coincidentes con los filtros.

---

## 11. Exportar resultados

Una vez aplicados los filtros del territorio o segmento de interés, descargue la lista resultante en Excel para entregarla al equipo de ventas o trabajarla externamente.

### Cómo exportar

1. Aplique los filtros deseados.
2. Haga clic en **`⬇ Exportar`** (botón amarillo-verde en la barra de filtros).
3. Se descargará automáticamente:

```
Territorios_Estrategicos_YYYY-MM-DD.xlsx
```

### Campos incluidos en el archivo exportado

| Campo | Descripción |
|---|---|
| `Score` | Puntaje de prioridad calculado |
| `Prioridad` | Categoría A, B o C |
| `Razon_Social` | Nombre legal |
| `NIT` | Número de identificación |
| `Ciudad` | Municipio |
| `Departamento` | Departamento |
| `Camara_Comercio` | Cámara de comercio |
| `Estado_Matricula` | Estado de la matrícula |
| `Antiguedad_Anos` | Años de antigüedad con un decimal |
| `Num_Fuentes` | Fuentes verificadas |
| `Dias_Para_Renovacion` | Días restantes *(negativo = ya venció)* |
| `Fecha_Renovacion` | Fecha de vencimiento |
| `Representante_Legal` | Nombre del representante |
| `Telefono` | Teléfono de contacto |
| `Email` | Correo electrónico |

> ⚠️ Se exportan **únicamente los registros visibles con los filtros activos**. Sin filtros, exporta el universo completo. El campo `Dias_Para_Renovacion` es especialmente útil para que el equipo de campo priorice las llamadas — valores negativos indican matrículas ya vencidas.

---

## 12. El Score de Prioridad — cómo se calcula

El **Score de Prioridad** es un indicador numérico entre **0 y 100 puntos** que estima el atractivo comercial de cada empresa como cliente potencial de cemento. Se calcula automáticamente al cargar el archivo Excel, sin intervención manual.

### Los tres componentes del Score

---

#### Componente 1 — Renovación de Matrícula `máximo 35 puntos`

| Días para renovación | Puntos | Lectura |
|---|---|---|
| 60 días o menos | **35 pts** | Urgencia máxima — contactar esta semana |
| 61 a 180 días | **18 pts** | Alta prioridad — contactar este mes |
| 181 a 365 días | **8 pts** | Prioridad media — ruta trimestral |
| Más de 365 días | **0 pts** | Sin urgencia inmediata |

> Una empresa próxima a renovar su matrícula está en plena revisión de costos y proveedores — ventana ideal para presentar una propuesta de cemento.

---

#### Componente 2 — Antigüedad de la Empresa `máximo 40 puntos`

| Antigüedad | Puntos | Lectura |
|---|---|---|
| 10 años o más | **40 pts** | Empresa consolidada — volúmenes y pago estables |
| 5 a 9 años | **30 pts** | Empresa madura — crecimiento sostenido |
| 2 a 4 años | **15 pts** | Empresa en desarrollo |
| Menos de 2 años | **5 pts** | Empresa nueva — mayor riesgo |

---

#### Componente 3 — Fuentes de Información `máximo 25 puntos`

```
Puntos = (num_fuentes ÷ 3) × 25
```

| Fuentes | Puntos |
|---|---|
| 3 | **25 pts** — Información completa |
| 2 | **≈ 17 pts** |
| 1 | **≈ 8 pts** |
| 0 | **0 pts** |

---

### Fórmula completa

```
Score = Pts_Renovación  +  Pts_Antigüedad  +  Pts_Fuentes
        (máx. 35)       +  (máx. 40)       +  (máx. 25)   =  máx. 100 pts
```

### Categorías de Prioridad

| Score | Prioridad | Acción recomendada |
|---|---|---|
| **≥ 70** | 🟢 **A — Alta** | Visita o llamada en la semana actual |
| **40 a 69** | 🟡 **B — Media** | Contacto planificado en el mes |
| **< 40** | 🔴 **C — Baja** | Seguimiento trimestral |

---

## 13. Estructura requerida del archivo Excel

Los datos deben estar en la **primera hoja del libro**, con los siguientes nombres de columna exactos en la fila 1:

| Campo | Tipo | Descripción | Impacto en Score |
|---|---|---|---|
| `id` | Texto | Identificador único del registro | — |
| `camara_comercio` | Texto | Nombre de la cámara de comercio | — |
| `razon_social` | Texto | Nombre legal de la empresa | — |
| `nit` | Texto/Número | NIT de la empresa | — |
| `estado_matricula` | Texto | `ACTIVA`, `INACTIVA` o `CANCELADA` | — |
| `fecha_matricula` | Fecha | Fecha de constitución o primera matrícula | ✅ Calcula antigüedad |
| `fecha_renovacion` | Fecha | Fecha de vencimiento de la matrícula | ✅ Calcula días para renovación |
| `representante_legal` | Texto | Nombre del representante legal | — |
| `ciudad` | Texto | Municipio de registro | — |
| `Departamento` | Texto | Departamento *(la **D** en mayúscula)* | — |
| `telefono` | Texto | Número de contacto | — |
| `email` | Texto | Correo electrónico | — |
| `lat` | Número | Latitud geográfica (ej: `4.6656`) | — *(necesario para mapa)* |
| `lng` | Número | Longitud geográfica (ej: `-74.1197`) | — *(necesario para mapa)* |
| `google_place_id` | Texto | ID de Google Places | — |
| `fecha_creacion` | Fecha | Fecha de creación del registro | — |
| `fecha_actualizacion` | Fecha | Última actualización | — |
| `ciclo_actualizacion` | Número | Periodicidad de actualización en días | — |
| `estado_info` | Texto | Estado de completitud de la información | — |
| `estado_legal` | Texto | Estado legal de la empresa | — |
| `estado_actividad` | Texto | Estado de actividad comercial | — |
| `formatted_address` | Texto | Dirección completa y estandarizada | — *(se muestra en mapa y tabla)* |
| `geocodificado` | Texto | `true` si tiene coordenadas, `false` si no | — |
| `num_fuentes` | Número | Fuentes verificadas (0 a 3) | ✅ Calcula componente fuentes |

### Notas importantes

- Los tres campos con ✅ son los que determinan el Score. Si están vacíos, se asigna el valor mínimo para ese componente.
- `lat` y `lng` son necesarios para que la empresa aparezca **en el mapa** con su tooltip de hover.
- `formatted_address` es la dirección que aparece en el **tooltip del mapa** al pasar el mouse, en la **ficha de clic** del mapa y en la **columna Dirección** de la tabla.
- `Departamento` debe tener la **D en mayúscula**.
- Columnas adicionales no reconocidas son ignoradas sin generar errores.
- Formatos aceptados: `.xlsx` (recomendado) y `.xls`.

---

## 14. Preguntas frecuentes

**¿El dashboard envía mis datos a algún servidor externo?**
No. Todo el procesamiento ocurre directamente en el navegador. Los datos nunca salen del computador. El archivo HTML es completamente autónomo.

**¿Por qué algunas empresas no aparecen en el mapa?**
Porque no tienen coordenadas geográficas válidas (`lat` / `lng`) dentro del rango de Colombia. Estas empresas sí aparecen en la tabla y en todos los KPIs con normalidad.

**¿Por qué al pasar el mouse sobre un punto del mapa el nombre aparece cortado?**
Es intencional. El tooltip está diseñado para ser compacto y legible. Al hacer **clic** sobre el punto se abre la ficha completa con el nombre sin recortar, la dirección completa y todos los datos de la empresa.

**¿Puedo usar el dashboard sin conexión a internet?**
Sí, con excepción del mapa. Los KPIs, filtros, gráficas y tabla funcionan completamente sin conexión. El fondo cartográfico del mapa requiere internet para visualizarse.

**Al seleccionar un departamento, ¿por qué cambia el listado de ciudades?**
Es el filtro encadenado. El selector de Ciudad se actualiza automáticamente para mostrar solo las ciudades con empresas en ese departamento, evitando selecciones vacías.

**¿Por qué el Score de algunas empresas es bajo?**
Por una o varias de estas razones: (1) la renovación está muy lejana, (2) la empresa es reciente, o (3) tiene pocas fuentes registradas. El campo `Dias_Para_Renovacion` del archivo exportado ayuda a identificar el caso.

**¿El botón Exportar descarga todos los registros o solo los filtrados?**
Solo los **registros visibles con los filtros activos en ese momento**. Sin filtros, exporta el total. Esto permite generar listas focalizadas por territorio, prioridad o cámara de comercio.

**¿Los datos persisten si cierro el navegador?**
No. Al cerrar o recargar, el tablero vuelve a la pantalla de bienvenida. Deberá cargar nuevamente el Excel. Los datos nunca se almacenan externamente — es una característica de seguridad de la herramienta.

**¿Puedo compartir el dashboard con otros usuarios del equipo?**
Sí. Comparta el archivo `RTM_Road_To_Market.html` y cada usuario lo abre en su propio navegador con su copia del Excel. No requiere instalación ni servidor compartido.

---

## 15. Glosario de términos

| Término | Definición |
|---|---|
| **Score** | Puntaje de 0 a 100 que indica el atractivo comercial de una empresa como cliente potencial de cemento. Se calcula automáticamente al cargar el archivo. |
| **Prioridad A** | Empresas con Score ≥ 70. Objetivo inmediato — contacto en la semana actual. |
| **Prioridad B** | Empresas con Score entre 40 y 69. Contacto planificado en el mes. |
| **Prioridad C** | Empresas con Score menor a 40. Seguimiento trimestral. |
| **KPI** | Key Performance Indicator — Indicador Clave de Desempeño. |
| **Tooltip** | Recuadro informativo que aparece al pasar el mouse sobre un elemento del mapa. Desaparece al mover el cursor. |
| **Ficha de empresa** | Panel detallado que se abre al hacer clic sobre un punto del mapa. Muestra todos los datos de esa empresa. |
| **Matrícula Mercantil** | Registro legal obligatorio de una empresa ante la Cámara de Comercio del territorio donde opera. |
| **Fecha de Renovación** | Fecha límite en que la empresa debe renovar su matrícula. |
| **Antigüedad** | Años desde la fecha de matrícula inicial hasta hoy. |
| **Num. Fuentes** | Número de fuentes de información verificadas sobre la empresa (0 a 3). |
| **Días para Renovación** | Días entre hoy y la fecha de renovación. Valor negativo = matrícula vencida. |
| **Formatted Address** | Dirección completa y estandarizada del establecimiento. Aparece en el tooltip del mapa y en la tabla. |
| **Geocodificado** | Indica si la empresa tiene coordenadas geográficas asignadas (`true` / `false`). |
| **Pipeline comercial** | Conjunto de oportunidades de venta en distintas etapas de seguimiento. |
| **Ventana crítica** | Período de 90 días o menos antes del vencimiento de la matrícula — momento óptimo para el contacto comercial. |
| **Filtro encadenado** | Mecanismo por el cual seleccionar Departamento actualiza automáticamente las opciones del filtro Ciudad. |

---

*Manual de Usuario · Dashboard RTM_Road_To_Market v1.0 · `RTM_Road_To_Market.html`*
*Inteligencia Comercial · Fuerza de Ventas · Materiales de Construcción*
