# 📊 Manual de Usuario — RTM_Road_To_Market
### Inteligencia Comercial · Materiales de Construcción

> **Versión:** 2.0 · **Archivo:** `RTM_Road_To_Market.html` · **Idioma:** Español colombiano

---

## Tabla de Contenidos

1. [¿Qué es este dashboard?](#1-qué-es-este-dashboard)
2. [Requisitos técnicos](#2-requisitos-técnicos)
3. [Cómo abrir el dashboard](#3-cómo-abrir-el-dashboard)
4. [Cargar o actualizar la base de datos](#4-cargar-o-actualizar-la-base-de-datos)
5. [Indicadores Clave — KPIs](#5-indicadores-clave--kpis)
6. [Filtros de búsqueda](#6-filtros-de-búsqueda)
7. [Mapa de territorios prioritarios](#7-mapa-de-territorios-prioritarios)
8. [Ranking de ciudades](#8-ranking-de-ciudades)
9. [Análisis multidimensional — Gráficas](#9-análisis-multidimensional--gráficas)
10. [Directorio de empresas — Tabla](#10-directorio-de-empresas--tabla)
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
- ¿Cuántos clientes potenciales activos hay por territorio?
- ¿Dónde están ubicadas geográficamente esas oportunidades?

El dashboard procesa el archivo Excel de la base de datos, calcula automáticamente un **Score de Prioridad** por empresa y presenta toda la información en un mapa interactivo, ranking de ciudades, gráficas de análisis y una tabla del directorio completo — todo desde un solo archivo `.html`, sin instalaciones adicionales.

---

## 2. Requisitos técnicos

| Elemento | Detalle |
|---|---|
| **Navegador web** | Google Chrome, Microsoft Edge o Mozilla Firefox (versión reciente) |
| **Conexión a internet** | Requerida únicamente para visualizar el mapa |
| **Archivo de datos** | Excel en formato `.xlsx` o `.xls` con la estructura definida en la [Sección 13](#13-estructura-requerida-del-archivo-excel) |
| **Instalaciones adicionales** | Ninguna — el dashboard es completamente autónomo |

> ⚠️ **No use Internet Explorer.** Use Chrome o Edge para garantizar el funcionamiento correcto de todas las funciones del tablero.

---

## 3. Cómo abrir el dashboard

1. Localice el archivo `RTM_Road_To_Market.html` en su computador.
2. Haga **doble clic** sobre él — se abrirá automáticamente en su navegador predeterminado.
3. Verá la pantalla de bienvenida con el mensaje *"Cargue su base de datos para iniciar"*.
4. Desde allí puede cargar su archivo Excel o explorar el tablero con datos de muestra haciendo clic en **"Cargar datos de muestra"**.

```
📁 RTM_Road_To_Market.html  ←  Doble clic para abrir
```

---

## 4. Cargar o actualizar la base de datos

### Cargar un archivo nuevo

**Paso 1 —** Haga clic en el botón **`Cargar / Actualizar Excel`** ubicado en la esquina superior derecha del encabezado (barra azul oscura).

**Paso 2 —** Se abrirá el explorador de archivos del sistema. Navegue hasta donde está guardado su archivo Excel y selecciónelo.

**Paso 3 —** Aparecerá brevemente un indicador de carga animado mientras el tablero procesa los registros.

**Paso 4 —** Al finalizar, todos los KPIs, el mapa, las gráficas, el ranking y la tabla se actualizarán automáticamente con la nueva información.

### Actualizar con un archivo más reciente

Haga clic nuevamente en **`Cargar / Actualizar Excel`** y seleccione el nuevo archivo. Los datos anteriores se reemplazarán en su totalidad.

### Usar los datos de muestra

En la pantalla de bienvenida, haga clic en **"Cargar datos de muestra"** para explorar todas las funciones del tablero con 10 registros reales de ferreterías en distintas ciudades de Colombia, sin necesidad de tener su archivo listo.

> 💡 El número total de registros cargados se muestra en la esquina superior derecha del encabezado, en color amarillo-verde, junto al texto **"Empresas cargadas"**.

---

## 5. Indicadores Clave — KPIs

Al cargar los datos, aparecen **6 tarjetas de KPIs** en la parte superior del tablero. Todos se actualizan en tiempo real cuando se aplican filtros.

| # | Tarjeta | Qué mide | Para qué sirve |
|---|---|---|---|
| 1 | 🏢 **Total Empresas** | Total de registros visibles con los filtros actuales | Dimensionar el universo de clientes potenciales en el territorio seleccionado |
| 2 | ✅ **Matrículas Activas** | Cantidad y porcentaje de empresas con estado `ACTIVA` | Identificar qué proporción del mercado está legalmente operativa |
| 3 | 🎯 **Prioridad Alta (A)** | Empresas con Score ≥ 70 puntos | **Lista crítica de contacto inmediato** para la fuerza de ventas — es el KPI más estratégico |
| 4 | 📈 **Score Promedio** | Promedio del Score de Prioridad del territorio o segmento filtrado | Medir el atractivo comercial general de una zona o región |
| 5 | 🔔 **Renovación ≤ 90 días** | Empresas cuya matrícula vence en los próximos 90 días | Ventana urgente de contacto — son empresas en proceso de revisión de proveedores |
| 6 | 📅 **Renovación ≤ 365 días** | Empresas dentro del pipeline del año calendario | Planificación del calendario de visitas y rutas comerciales anuales |

> 🎯 La tarjeta **Prioridad Alta (A)** se resalta con borde superior amarillo-verde y lleva la etiqueta **CRÍTICO** — es el indicador más importante para priorizar las acciones de venta.

---

## 6. Filtros de búsqueda

La barra de filtros permite segmentar los datos para enfocarse en territorios, empresas o segmentos específicos. **Todo el tablero** (KPIs, mapa, ranking, gráficas y tabla) se actualiza instantáneamente al aplicar cualquier filtro.

### Filtros disponibles

| Filtro | Función | Comportamiento especial |
|---|---|---|
| **Departamento** | Muestra solo empresas del departamento seleccionado | Al cambiar el departamento, el filtro de **Ciudad se actualiza automáticamente** mostrando solo las ciudades de ese departamento |
| **Ciudad** | Filtra por municipio específico | Depende del departamento seleccionado. Si no hay departamento elegido, muestra todas las ciudades disponibles |
| **Cámara de Comercio** | Segmenta por la cámara de comercio de origen del registro | Independiente de los demás filtros |
| **Estado Matrícula** | Filtra por `ACTIVA`, `INACTIVA` o `CANCELADA` | — |
| **Prioridad Score** | Muestra solo empresas de la categoría elegida: A, B o C | — |
| **Buscar Razón Social / NIT** | Búsqueda libre por nombre de empresa o número de NIT | Busca en tiempo real mientras escribe |

### Filtro encadenado: Departamento → Ciudad

Esta es una funcionalidad clave del tablero. Al seleccionar un **Departamento**, el desplegable de **Ciudad** se repuebla automáticamente mostrando únicamente las ciudades que pertenecen a ese departamento. Si luego cambia de departamento y la ciudad anterior no corresponde al nuevo, el campo Ciudad se limpia automáticamente.

### Botones de acción

- **`✕ Limpiar`** — Restablece todos los filtros a su estado inicial y muestra el universo completo de datos.
- **`⬇ Exportar`** — Descarga en Excel los registros actualmente filtrados. Ver [Sección 11](#11-exportar-resultados).

### Ejemplo de análisis territorial

> *Quiero que la fuerza de ventas enfoque esta semana en Antioquia, visitando solo ferreterías activas de alta prioridad.*
>
> 1. Seleccione **Departamento → Antioquia**
> 2. El filtro Ciudad se actualiza con los municipios de Antioquia
> 3. Seleccione **Estado Matrícula → ACTIVA**
> 4. Seleccione **Prioridad Score → A — Alta (≥70)**
>
> El mapa, el ranking y la tabla mostrarán exclusivamente esas oportunidades. Use **`⬇ Exportar`** para entregar la lista al equipo de campo.

---

## 7. Mapa de territorios prioritarios

El mapa muestra geográficamente la distribución de empresas en Colombia, **agrupadas por ciudad**, y se actualiza con cada filtro aplicado.

### Lectura del mapa

**Color del punto — indica el Score promedio de la ciudad:**

| Color | Score promedio | Significado |
|---|---|---|
| 🟡 **Amarillo-verde** | ≥ 70 puntos | Prioridad Alta — territorio de acción inmediata |
| 🟠 **Naranja** | 40 a 69 puntos | Prioridad Media — planificar visitas este mes |
| 🔴 **Rojo** | < 40 puntos | Prioridad Baja — seguimiento trimestral |

**Tamaño del punto:** proporcional al número de empresas registradas en esa ciudad. A mayor tamaño, mayor concentración de clientes potenciales.

**Indicador de ciudades:** en la esquina superior derecha del mapa muestra cuántas ciudades están siendo visualizadas con los filtros activos.

### Interacción con el mapa

| Acción | Resultado |
|---|---|
| **Clic en un punto** | Abre un panel emergente con el detalle de la ciudad: nombre, departamento, total de empresas, desglose por prioridad (A / B / C) y Score promedio |
| **Rueda del mouse** | Zoom de acercamiento o alejamiento |
| **Clic + arrastrar** | Desplazamiento por el mapa |
| **Botones `+` / `−`** | Zoom controlado (esquina superior izquierda) |

> ℹ️ Solo aparecen en el mapa las empresas que tienen coordenadas geográficas válidas (`lat` y `lng`) dentro del rango geográfico de Colombia. Las que no tienen coordenadas aparecen en la tabla pero no en el mapa.

> 🌐 El mapa requiere conexión a internet para cargar el fondo cartográfico (OpenStreetMap / CARTO). Sin internet, el resto del tablero funciona con normalidad.

---

## 8. Ranking de ciudades

El panel lateral derecho de la sección **Distribución Geográfica & Ranking** muestra el **Top 15 de ciudades** ordenadas de mayor a menor Score promedio, actualizadas con los filtros activos.

### Cómo leer el ranking

| Elemento | Significado |
|---|---|
| **Número de posición** | Lugar en el ranking (1 = mejor Score promedio) |
| **Fondo dorado** | Las 3 primeras posiciones — territorios de máxima oportunidad |
| **Nombre y departamento** | Ciudad con la cantidad de empresas registradas |
| **Número a la derecha** | Score promedio de todas las empresas de esa ciudad |
| **Barra inferior** | Representa visualmente el Score relativo al líder del ranking |

Las ciudades en las primeras posiciones deben recibir **visita o contacto prioritario** de la fuerza de ventas en el período inmediato.

---

## 9. Análisis multidimensional — Gráficas

Esta sección presenta **dos gráficas complementarias** que se actualizan con cada filtro aplicado. Permiten analizar los datos desde distintas dimensiones para tomar decisiones de asignación de recursos de ventas.

---

### 📊 Gráfica 1 — Score Promedio por Departamento

**Tipo:** Barras horizontales

Muestra los **8 departamentos con mayor Score promedio**, ordenados de mayor a menor. El valor numérico aparece al final de cada barra.

**Para qué sirve:** Identificar en qué regiones del país concentrar los recursos de ventas en primer lugar. Los departamentos con barras más largas ofrecen el mayor retorno esperado por visita comercial.

---

### 🎯 Gráfica 2 — Distribución por Prioridad

**Tipo:** Barras de progreso por categoría

Muestra cuántas empresas hay en cada categoría de prioridad (A, B, C) y qué porcentaje representan sobre el total filtrado.

| Barra | Color | Categoría |
|---|---|---|
| **A** | Amarillo-verde | Prioridad Alta — Score ≥ 70 |
| **B** | Naranja | Prioridad Media — Score 40 a 69 |
| **C** | Rojo | Prioridad Baja — Score < 40 |

**Para qué sirve:** Dimensionar la carga de trabajo del equipo comercial por zona, distribuir la fuerza de ventas según la densidad de cada prioridad, y planificar rutas de visita por intensidad de oportunidad.

---

## 10. Directorio de empresas — Tabla

La tabla muestra el directorio completo de empresas del territorio filtrado, con toda la información necesaria para la gestión comercial directa.

### Columnas de la tabla

| Columna | Descripción | Indicadores visuales |
|---|---|---|
| **Score** | Puntaje de prioridad calculado automáticamente (0–100) | 🟢 Verde ≥ 70 · 🟡 Amarillo 40–69 · 🔴 Rojo < 40 |
| **Prio.** | Categoría de prioridad asignada | ● A (verde) · ● B (naranja) · ● C (rojo) |
| **Razón Social** | Nombre legal de la empresa | Texto con tooltip al pasar el cursor cuando es largo |
| **NIT** | Número de identificación tributaria | — |
| **Ciudad** | Municipio de registro | — |
| **Departamento** | Departamento de registro | — |
| **Cámara Comercio** | Cámara que expidió la matrícula | Texto con tooltip cuando es largo |
| **Estado** | Estado de la matrícula mercantil | 🟢 ACTIVA · 🔴 INACTIVA · 🟡 Otros |
| **Antigüedad** | Años desde la fecha de matrícula inicial | Expresado con un decimal (ej: `12.3 años`) |
| **Fuentes** | Número de fuentes de información verificadas | Valor numérico (máximo 3) |
| **Renovación** | Fecha de vencimiento de la matrícula | Formato DD/MM/AAAA |
| **Representante** | Nombre del representante legal | Texto con tooltip cuando es largo |
| **Dirección** | Dirección completa formateada del establecimiento | Texto en gris, con tooltip al pasar el cursor |

### Ordenar la tabla

Haga clic en el **encabezado de cualquier columna** para ordenar por ese campo en orden descendente. Un segundo clic invierte el orden a ascendente. La columna activa se resalta en color amarillo-verde con una flecha indicadora (↑ ↓).

> 💡 **Tip estratégico:** Ordene por **Score descendente** para tener al tope de la lista las empresas con mayor potencial comercial — esas son las primeras visitas que debe asignar al equipo de ventas.

### Navegación por páginas

La tabla muestra **20 registros por página**. Use los controles de paginación en la parte inferior derecha (`‹ 1 2 3 … ›`) para navegar entre páginas. El contador inferior izquierdo indica el rango visible y el total de registros que coinciden con los filtros activos.

---

## 11. Exportar resultados

Una vez aplicados los filtros del territorio o segmento de interés, puede descargar la lista resultante en Excel para compartirla con el equipo de ventas o trabajarla por fuera del dashboard.

### Cómo exportar

1. Aplique los filtros deseados en la barra de búsqueda.
2. Haga clic en el botón **`⬇ Exportar`** (color amarillo-verde en la barra de filtros).
3. Se descargará automáticamente un archivo Excel con el nombre:

```
Territorios_Estrategicos_YYYY-MM-DD.xlsx
```

### Campos incluidos en el archivo exportado

| Campo | Descripción |
|---|---|
| `Score` | Puntaje de prioridad calculado |
| `Prioridad` | Categoría A, B o C |
| `Razon_Social` | Nombre legal de la empresa |
| `NIT` | Número de identificación tributaria |
| `Ciudad` | Municipio |
| `Departamento` | Departamento |
| `Camara_Comercio` | Cámara de comercio |
| `Estado_Matricula` | Estado de la matrícula |
| `Antiguedad_Anos` | Años de antigüedad con un decimal |
| `Num_Fuentes` | Número de fuentes verificadas |
| `Dias_Para_Renovacion` | Días restantes (negativo = ya venció) |
| `Fecha_Renovacion` | Fecha de vencimiento de matrícula |
| `Representante_Legal` | Nombre del representante |
| `Telefono` | Teléfono de contacto |
| `Email` | Correo electrónico |

> ⚠️ El botón exporta **únicamente los registros visibles según los filtros activos**. Si no hay filtros aplicados, exporta el universo completo. Esto permite generar listas focalizadas por territorio, prioridad o cámara de comercio listas para entregar al equipo de campo.

---

## 12. El Score de Prioridad — cómo se calcula

El **Score de Prioridad** es un indicador numérico entre **0 y 100 puntos** que estima el atractivo comercial de cada empresa como cliente potencial de cemento. Se calcula automáticamente para cada registro al cargar el archivo Excel.

### Los tres componentes del Score

---

#### Componente 1 — Renovación de Matrícula `(máximo 35 puntos)`

Mide la urgencia de contacto según los días que faltan para que venza la matrícula mercantil.

| Días para renovación | Puntos | Lectura estratégica |
|---|---|---|
| 60 días o menos | **35 pts** | Urgencia máxima — contacto esta semana |
| 61 a 180 días | **18 pts** | Alta prioridad — contacto este mes |
| 181 a 365 días | **8 pts** | Prioridad media — ruta trimestral |
| Más de 365 días | **0 pts** | Sin urgencia inmediata |

> Una empresa próxima a renovar su matrícula está en un momento natural de revisión de costos y proveedores — es la ventana ideal para presentar una propuesta de venta de cemento.

---

#### Componente 2 — Antigüedad de la Empresa `(máximo 40 puntos)`

Mide la solidez y trayectoria del negocio según los años transcurridos desde su constitución.

| Antigüedad | Puntos | Lectura estratégica |
|---|---|---|
| 10 años o más | **40 pts** | Empresa consolidada — volúmenes y capacidad de pago estables |
| 5 a 9 años | **30 pts** | Empresa madura — crecimiento sostenido |
| 2 a 4 años | **15 pts** | Empresa en desarrollo |
| Menos de 2 años | **5 pts** | Empresa nueva — mayor riesgo comercial |

> Las empresas más antiguas tienen historial crediticio establecido y mayor volumen habitual de compra de materiales de construcción.

---

#### Componente 3 — Fuentes de Información `(máximo 25 puntos)`

Mide la completitud y verificabilidad del registro en la base de datos.

```
Puntos = (num_fuentes ÷ 3) × 25
```

| Fuentes registradas | Puntos |
|---|---|
| 3 fuentes | **25 pts** — Información completa y verificada |
| 2 fuentes | **≈ 17 pts** |
| 1 fuente | **≈ 8 pts** |
| 0 fuentes | **0 pts** |

> A mayor número de fuentes, más visible y confiable es la empresa en el mercado, reduciendo el riesgo de la visita comercial.

---

### Fórmula completa

```
Score = Pts_Renovación  +  Pts_Antigüedad  +  Pts_Fuentes
Score =   (máx. 35)    +    (máx. 40)     +   (máx. 25)   =  máx. 100 puntos
```

### Categorías de Prioridad resultantes

| Score | Prioridad | Color | Acción recomendada |
|---|---|---|---|
| **≥ 70 puntos** | **A — Alta** | 🟢 Verde | Visita o llamada en la semana actual |
| **40 a 69 puntos** | **B — Media** | 🟡 Amarillo | Planificar contacto en el mes en curso |
| **< 40 puntos** | **C — Baja** | 🔴 Rojo | Seguimiento trimestral |

---

## 13. Estructura requerida del archivo Excel

El archivo debe tener los datos en la **primera hoja del libro**, con los siguientes nombres de columna exactos en la fila de encabezado (fila 1):

| Campo | Tipo | Descripción | Impacto en Score |
|---|---|---|---|
| `id` | Texto | Identificador único del registro | — |
| `camara_comercio` | Texto | Nombre de la cámara de comercio | — |
| `razon_social` | Texto | Nombre legal de la empresa | — |
| `nit` | Texto / Número | NIT de la empresa | — |
| `estado_matricula` | Texto | `ACTIVA`, `INACTIVA` o `CANCELADA` | — |
| `fecha_matricula` | Fecha | Fecha de constitución o primera matrícula | ✅ Calcula antigüedad |
| `fecha_renovacion` | Fecha | Fecha de vencimiento de la matrícula | ✅ Calcula días para renovación |
| `representante_legal` | Texto | Nombre completo del representante legal | — |
| `ciudad` | Texto | Municipio de registro | — |
| `Departamento` | Texto | Departamento *(la **D** debe ir en mayúscula)* | — |
| `telefono` | Texto | Número de contacto principal | — |
| `email` | Texto | Correo electrónico de contacto | — |
| `lat` | Número | Latitud geográfica (ej: `4.6656`) | — *(necesario para mapa)* |
| `lng` | Número | Longitud geográfica (ej: `-74.1197`) | — *(necesario para mapa)* |
| `google_place_id` | Texto | ID de Google Places | — |
| `fecha_creacion` | Fecha | Fecha de creación del registro | — |
| `fecha_actualizacion` | Fecha | Última actualización del registro | — |
| `ciclo_actualizacion` | Número | Periodicidad de actualización en días | — |
| `estado_info` | Texto | Estado de completitud de la información | — |
| `estado_legal` | Texto | Estado legal de la empresa | — |
| `estado_actividad` | Texto | Estado de actividad comercial | — |
| `formatted_address` | Texto | Dirección completa y formateada | — *(se muestra en tabla)* |
| `geocodificado` | Texto | `true` si tiene coordenadas, `false` si no | — |
| `num_fuentes` | Número | Fuentes de información verificadas (0 a 3) | ✅ Calcula componente fuentes |

### Consideraciones importantes sobre el archivo

- Los campos marcados con ✅ son los que determinan el Score. Si están vacíos, se asigna el valor mínimo para ese componente.
- Los campos `lat` y `lng` son necesarios para que la empresa aparezca **en el mapa**. Sin ellos, el registro aparece en la tabla pero no en el mapa.
- El campo `Departamento` debe tener la **D en mayúscula** tal como aparece en la base de datos original.
- Columnas adicionales no reconocidas son ignoradas sin generar errores.
- El archivo puede estar en formato `.xlsx` (recomendado) o `.xls`.

---

## 14. Preguntas frecuentes

**¿El dashboard envía mis datos a algún servidor externo?**
No. Todo el procesamiento ocurre directamente en el navegador del usuario. Los datos nunca salen del computador. El archivo HTML es completamente autónomo.

**¿Por qué algunas empresas no aparecen en el mapa?**
Porque no tienen coordenadas geográficas (`lat` / `lng`) registradas en el archivo, o sus coordenadas están fuera del rango geográfico válido de Colombia. Estas empresas aparecen correctamente en la tabla y en todos los KPIs.

**¿Puedo usar el dashboard sin conexión a internet?**
Sí, con excepción del mapa. Los KPIs, los filtros, las gráficas y la tabla funcionan completamente sin conexión. El fondo cartográfico del mapa requiere internet para visualizarse.

**Al seleccionar un departamento, ¿por qué cambia el listado de ciudades?**
Es el filtro encadenado. Al elegir un departamento, el selector de ciudad se actualiza automáticamente para mostrar solo las ciudades con empresas registradas en ese departamento, evitando selecciones sin resultados.

**¿Por qué el Score de algunas empresas es muy bajo?**
Hay tres razones posibles: (1) la fecha de renovación está muy lejana, (2) la empresa es reciente y tiene poca antigüedad, o (3) tiene pocas fuentes de información registradas. Revise cada componente para identificar cuál limita el puntaje.

**¿El botón Exportar descarga todos los datos o solo los filtrados?**
Solo exporta los registros **visibles según los filtros activos en ese momento**. Si no hay filtros aplicados, exporta el total. Esto permite generar listas de trabajo focalizadas por territorio.

**¿Puedo compartir el dashboard con otros miembros del equipo?**
Sí. Comparta el archivo `RTM_Road_To_Market.html` junto con el archivo Excel. Cada usuario puede cargarlo en su propio navegador de forma independiente, sin instalación ni acceso a servidores compartidos.

**¿Los datos cargados persisten si cierro el navegador?**
No. Al cerrar o recargar el navegador, el tablero vuelve a la pantalla de bienvenida y deberá cargarse nuevamente el archivo Excel. Los datos nunca se almacenan externamente — esta es una característica de seguridad de la herramienta.

**¿Qué tamaño máximo de archivo puede procesar el dashboard?**
Está optimizado para archivos de hasta aproximadamente 50.000 registros. Para bases más grandes, el procesamiento inicial puede tardar algunos segundos adicionales según el rendimiento del equipo.

**¿Qué ocurre si el archivo Excel tiene columnas adicionales?**
Las columnas no reconocidas son ignoradas completamente. No generan errores ni afectan el funcionamiento del tablero.

---

## 15. Glosario de términos

| Término | Definición |
|---|---|
| **Score** | Puntaje de 0 a 100 puntos que indica el atractivo comercial de una empresa como cliente potencial de cemento. Se calcula automáticamente al cargar el archivo. |
| **Prioridad A** | Empresas con Score ≥ 70. Objetivo inmediato de la fuerza de ventas — contacto en la semana actual. |
| **Prioridad B** | Empresas con Score entre 40 y 69. Contacto planificado dentro del mes en curso. |
| **Prioridad C** | Empresas con Score menor a 40. Inclusión en campaña de seguimiento trimestral. |
| **KPI** | Key Performance Indicator. Indicador Clave de Desempeño — métrica que resume el estado de una dimensión estratégica del negocio. |
| **Matrícula Mercantil** | Registro legal obligatorio de una empresa ante la Cámara de Comercio del territorio donde opera. |
| **Fecha de Renovación** | Fecha límite en que la empresa debe renovar su matrícula ante la Cámara de Comercio. |
| **Antigüedad** | Años transcurridos desde la fecha de matrícula inicial de la empresa hasta la fecha actual. |
| **Num. Fuentes** | Número de fuentes de información verificadas sobre la empresa en la base de datos. Valor entre 0 y 3. |
| **Días para Renovación** | Diferencia en días entre la fecha actual y la fecha de renovación. Valor negativo indica que la matrícula ya está vencida. |
| **Formatted Address** | Dirección completa y estandarizada del establecimiento, obtenida del proceso de geocodificación. |
| **Geocodificado** | Indica si la empresa tiene coordenadas geográficas (latitud/longitud) asignadas. Valor `true` o `false`. |
| **Pipeline comercial** | Conjunto de oportunidades de venta identificadas que están en distintas etapas de seguimiento. |
| **Ventana crítica** | Período de 90 días o menos antes del vencimiento de una matrícula — momento óptimo para el contacto comercial. |
| **Filtro encadenado** | Mecanismo en el que seleccionar un valor en un filtro actualiza automáticamente las opciones de otro filtro relacionado (Departamento → Ciudad). |

---

## Contacto y soporte

Para reportar errores, solicitar nuevas funcionalidades o consultas sobre la interpretación de los indicadores y el Score, contacte al equipo responsable de inteligencia comercial o al administrador técnico de la herramienta.

---

*Manual de Usuario · Dashboard RTM_Road_To_Market v1.0 · `RTM_Road_To_Market.html`*
*Herramienta de Inteligencia Comercial · Fuerza de Ventas · Materiales de Construcción*
