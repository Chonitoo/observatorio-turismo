# Propuesta del Observatorio — E0

**Observatorio de Ocupación Hotelera de Colima (OOH-Colima)**
Autor: Maximiliano Encarnación Velázquez Rodríguez · Repositorio: `github.com/Chonitoo/observatorio-turismo` · Fecha: noviembre 2026

---

## 1. Ficha del observatorio

| Campo | Definición |
|---|---|
| **Sector económico** | Turismo — servicios de alojamiento temporal (SCIAN 721, hoteles y moteles). |
| **Región** | Estado de Colima: **Manzanillo** (centro de playa, unidad principal) y **Colima capital** (centro de ciudad, unidad de contraste). Para comparar se usan los demás centros de playa del Pacífico mexicano. |
| **Unidad de observación** | Destino turístico × categoría hotelera (1 a 5 estrellas) × mes. |
| **Periodo inicial** | Enero 2016 – diciembre 2024: **108 periodos mensuales** (requisito mínimo: 36). |
| **Pregunta detonadora** | *¿Por qué los hoteles de Manzanillo llenan apenas la mitad de sus cuartos y cuánto ocuparán en los próximos 12 meses, si destinos comparables del Pacífico superan el 60 %?* |
| **Cliente potencial** | Hoteleros de Manzanillo y su asociación gremial (planeación de tarifas, personal temporal y compras), así como la Secretaría de Turismo del Estado de Colima (promoción y política de temporadas). |
| **Decisión que habilita** | Cuánto personal contratar y qué tarifas ofrecer cada mes; cuándo lanzar campañas para levantar la temporada baja (septiembre–octubre); a qué mercado dirigir la promoción (nacional o extranjero). |

### 1.1 Por qué este problema importa (evidencia preliminar de los datos crudos)

Un primer análisis exploratorio de la serie DataTur (capa Bronce, sin limpieza) muestra cuatro hechos que justifican el observatorio:

1. **Ocupación baja respecto a sus pares.** De 2016 a 2024 la ocupación promedio de Manzanillo fue **45.3 %**. Puerto Vallarta llegó a 66.6 %, Nuevo Nayarit a 67.4 %, Mazatlán a 59.7 % e Ixtapa-Zihuatanejo a 54.3 %. Entre los 19 centros de playa monitoreados, Manzanillo ocupa el lugar 12.
2. **Estacionalidad marcada.** La ocupación de Manzanillo sube a 53.6 % en julio y 53.7 % en diciembre, y cae a **33.8 % en septiembre**, una diferencia de 20 puntos.
3. **Dependencia casi total del turismo nacional.** Sólo entre 2.5 % y 4.6 % de las llegadas son de turistas no residentes en México.
4. **Visitas cada vez más cortas.** La estadía promedio bajó de **2.75 noches (2016) a 2.00 noches (2024)**, aunque las llegadas crecieron de 610 mil a más de un millón por año. Llega más gente, pero se queda menos.

| Año | Ocupación Manzanillo (%) | Llegadas Manzanillo | Estadía (noches) | Ocupación Colima capital (%) |
|---|---|---|---|---|
| 2016 | 47.3 | 610,264 | 2.75 | 43.7 |
| 2019 | 46.5 | 937,343 | 2.23 | 45.0 |
| 2020 | 23.2 | 531,424 | 1.94 | 22.9 |
| 2022 | 48.4 | 1,104,867 | 1.82 | 37.8 |
| 2023 | 55.4 | 1,236,340 | 1.90 | 42.2 |
| 2024 | 54.7 | 1,066,546 | 2.00 | 44.0 |

*Fuente: SECTUR-DataTur, Base70centros.csv; ocupación = cuartos ocupados (residentes + no residentes) / cuartos disponibles.*

---

## 2. Entrevista de campo

### 2.1 Datos de la entrevista

| Campo | Valor |
|---|---|
| Persona entrevistada (nombre o iniciales, con su consentimiento) | Lic. R. M. G. |
| Puesto y organización | Gerente de Operaciones y Reservaciones, Hotel 4★ (zona Costera / Playa Azul, Manzanillo) |
| Años de experiencia en el sector | 14 años en hotelería de playa en el Pacífico mexicano (8 años en Manzanillo) |
| Fecha, medio y duración | 10/11/2026 · Llamada telefónica · 22 min |
| Consentimiento | Se le informó que la entrevista es para un proyecto académico y que sus respuestas se publicarán sin datos sensibles. Sí |

### 2.2 Guion: 5 preguntas y respuestas

| # | Pregunta | Qué busca validar | Respuesta (resumen) |
|---|---|---|---|
| 1 | ¿Cómo describe un año típico de ocupación en su hotel? ¿Cuáles son los meses más llenos y los más vacíos, y por qué cree que pasa? | Que la estacionalidad (pico jul/dic, valle en sep) coincida con su experiencia. | Los números reflejan tal cual nuestra realidad operativa. Julio y agosto por el periodo vacacional escolar de verano, junto con la segunda quincena de diciembre y las semanas de Santa y Pascua, son nuestros techos de ocupación (alcanzamos 80–90 % en fines de semana). En contraste, septiembre y octubre son meses de supervivencia donde caemos a niveles del 30–35 %. La causa es doble: el gasto de las familias en el regreso a clases que contrae el turismo, sumado a la temporada alta de lluvias y ciclones en el Pacífico. Esos meses los aprovechamos forzosamente para dar vacaciones al personal y hacer mantenimiento preventivo a habitaciones. |
| 2 | ¿Con cuánta anticipación decide cuánto personal contratar, cuánto comprar y qué tarifas ofrecer? ¿Qué información usa hoy para esas decisiones? | Que un pronóstico de 3 a 12 meses le sirva y que hoy no lo tienen (necesidad del cliente). | Actualmente planificamos compras y plantilla de personal eventual (camaristas, cocineros, meseros) con apenas 3 o 4 semanas de anticipación, basándonos en el ritmo de reservaciones que van entrando al sistema (pickup) y comparando empíricamente con el mismo mes del año pasado. No contamos con modelos predictivos formales. Disponer de un pronóstico certero a 3, 6 y 12 meses resolvería dos problemas graves: evitar pagar horas extras no presupuestadas ante llegadas imprevistas, y evitar sobrecontratar personal eventual en semanas bajas donde nos vemos forzados a rematar tarifas a última hora perjudicando el RevPAR. |
| 3 | ¿De dónde vienen principalmente sus huéspedes (Guadalajara, Bajío, CDMX, extranjero)? ¿Ha cambiado eso en los últimos años? | Dependencia del turismo nacional; posibles factores (carreteras, vuelos, tipo de cambio). | Entre el 85 % y 90 % de los huéspedes corresponden a turismo nacional carretero. Nuestro mercado natural por cercanía geográfica es la Zona Metropolitana de Guadalajara (a 3.5–4 horas por autopista), seguido de León, Aguascalientes, Morelia y un porcentaje menor de CDMX. El turismo extranjero es mínimo (3 % a 4 %), concentrado en canadienses y estadounidenses jubilados que llegan en vuelos chárter de invierno. La razón principal de no captar más extranjero es que la conectividad aérea del aeropuerto de Manzanillo (ZLO) es muy reducida y costosa en comparación con destinos como Vallarta o Guadalajara. |
| 4 | Hemos visto que la estadía promedio bajó de casi 3 a 2 noches. ¿Lo nota usted? ¿A qué lo atribuye (fines de semana, plataformas como Airbnb, precios, seguridad)? | Explicar la caída de la estadía; descubrir factores para E2. | Es una realidad palpable: Manzanillo se ha transformado en un destino de fin de semana exprés. Al estar tan accesible por autopista desde Jalisco y el Bajío, el visitante llega el viernes por la tarde y realiza el check-out el domingo al mediodía (2 noches exactas). Antes las familias reservaban estancias de 4 a 5 días. Además, la proliferación de casas y departamentos en renta vacacional (Airbnb y similares) en áreas como Santiago, Las Hadas y La Boquita ha absorbido las estancias familiares largas, dejando a la hotelería tradicional dependiente del turismo de escapada corta. |
| 5 | ¿Con qué destinos compite Manzanillo (Vallarta, Mazatlán, Ixtapa...)? ¿Qué tienen ellos que Manzanillo no tiene? | Elegir los grupos de comparación multivariada (E3) y las variables relevantes. | Competimos de manera directa con Ixtapa-Zihuatanejo y Puerto Vallarta, y en la zona del Bajío con Mazatlán. Vallarta y Mazatlán nos superan ampliamente en tres factores: conectividad aérea internacional masiva, una oferta de vida nocturna y gastronómica mucho más variada, y una identidad volcada al 100 % al turismo. Manzanillo conserva una imagen dividida entre su vocación de puerto comercial/industrial de carga y su franja turística, lo que nos empuja a competir por precio y cercanía carretera antes que por oferta de destino o lujo. |

### 2.3 Aprendizajes y ajustes al observatorio

1. **Confirmación empírica de la estacionalidad:** La experiencia en piso valida por completo que el desplome de septiembre (33.8 %) obedece al impacto del gasto familiar en el regreso a clases y a la temporada de ciclones, mientras que la reducción de la estadía a 2.0 noches se explica por la hegemonía del turismo carretero de fin de semana (viernes a domingo) y el desplazamiento de estancias largas hacia plataformas de renta vacacional.
2. **Incorporación de factores en E2:** Se identificó la necesidad de incorporar en el diseño experimental el impacto de los **fines de semana largos / puentes oficiales**, así como la **estacionalidad climática (temporada de ciclones/lluvias)** como componentes críticos que modulan la ocupación más allá de los meses vacacionales escolares estándar.
3. **Focalización del cliente y aplicación de E1:** Se ratificó que las asociaciones de hoteles y gerencias operativas carecen de herramientas formales de pronóstico; el modelo de E1 tiene valor directo para definir la contratación de personal temporal y programación de compras de insumos en horizontes de 1 a 3 meses (operativo) y tarifas base a 6–12 meses (estratégico).

**Ajuste realizado a la propuesta:** Se formalizó la inclusión de los *puentes y días festivos oficiales* como componente relevante del factor Temporada en E2, y se afinó la aplicación práctica del pronóstico de E1 orientada a la planeación de compras anticipadas y contratos de personal eventual en categorías hoteleras de 3 a 5 estrellas.

---

## 3. Las tres preguntas analíticas

### E1 — Pronóstico (variable a pronosticar)

**Pregunta:** *¿Cuál será el porcentaje mensual de ocupación hotelera de Manzanillo en los próximos 12 meses, con un intervalo de confianza del 95 %?*

- **Variable objetivo (Y):** `ocupacion_pct = (cuartos_ocupados_residentes + cuartos_ocupados_no_residentes) / cuartos_disponibles × 100`, agregada por mes para todo el destino.
- **Serie:** 108 meses (2016-01 a 2024-12), con capturas nuevas cada mes. Tiene estacionalidad anual clara (s = 12) y un choque estructural en 2020 (COVID-19).
- **Modelos candidatos:** ingenuo estacional (línea base), suavizamiento exponencial Holt-Winters, SARIMA y SARIMAX con regresores exógenos (tipo de cambio, variable indicadora de pandemia).
- **Validación:** ventana deslizante con los últimos 12 meses como prueba; métricas MAE, RMSE y MAPE. El modelo debe superar al ingenuo estacional.
- **Variables secundarias que también se podrán pronosticar:** llegadas totales de turistas y estadía promedio.

### E2 — Diseño de experimentos (factores a experimentar)

**Pregunta:** *¿Qué factores, y qué interacciones entre ellos, explican las diferencias en la ocupación hotelera de Colima?*

Se trata como un diseño factorial observacional y se analiza con ANOVA multifactorial (y su alternativa no paramétrica si no se cumplen los supuestos):

| Factor | Niveles | Hipótesis |
|---|---|---|
| A. **Tipo de destino** | Playa (Manzanillo) · Ciudad (Colima) | La playa tiene más ocupación y más estacionalidad. |
| B. **Categoría hotelera** | 1-2★ · 3★ · 4★ · 5★ | Las categorías altas tienen más ocupación (hoteles de cadena y paquetes). |
| C. **Temporada** | Alta (abr, jul, ago, dic) · Baja (sep, oct) · Media (resto) | La temporada explica la mayor parte de la varianza. |
| D. **Periodo** | Prepandemia (2016-2019) · Pandemia (2020-2021) · Pospandemia (2022-2024) | La pandemia cambió el nivel y el patrón (interacción C×D). |

- **Respuesta:** `ocupacion_pct` por destino × categoría × mes.
- **Covariables:** tipo de cambio FIX y la inflación (INPC) de Banxico, para probar si un peso débil impulsa el turismo nacional (ANCOVA).
- **Interacciones de interés:** A×C (¿la ciudad es menos estacional?) y B×D (¿qué categorías se recuperaron mejor después de la pandemia?).

### E3 — Análisis multivariado (grupos a comparar)

**Pregunta:** *¿Manzanillo se parece más a los destinos de playa exitosos del Pacífico o a los rezagados? ¿Qué combinación de indicadores lo separa de ellos?*

- **Grupos:**
  1. **Pacífico líder:** Puerto Vallarta, Nuevo Nayarit, Los Cabos, Mazatlán.
  2. **Pacífico intermedio:** Manzanillo, Ixtapa-Zihuatanejo, Bahías de Huatulco, La Paz.
  3. **Pacífico rezagado:** Acapulco, Puerto Escondido, Loreto.
- **Vector de variables por destino y mes:** ocupación (%), estadía promedio (noches), densidad (turistas por cuarto ocupado), proporción de turistas no residentes (%) y oferta (cuartos disponibles).
- **Técnicas:** MANOVA para probar si los grupos difieren en conjunto; análisis de componentes principales (PCA) para ver dónde se ubica Manzanillo; análisis discriminante y clúster jerárquico para comprobar si el agrupamiento propuesto coincide con el que surge de los datos.

---

## 4. Plan de recopilación de datos

### 4.1 Fuentes

| # | Fuente | Contenido | Formato y acceso | Frecuencia | Uso |
|---|---|---|---|---|---|
| 1 | **SECTUR – DataTur**, *Ocupación hotelera en los 70 destinos principales* ([ficha en datos.gob.mx](https://www.datos.gob.mx/dataset/ocupacion_hotelera_70_destinos_principales_monitoreados_datatur)) | Cuartos disponibles y ocupados, llegadas y turistas-noche (residentes y no residentes) por destino, categoría y mes. 31,147 registros, 2016-2024. | CSV separado por tabuladores, descarga directa: `repodatos.atdt.gob.mx/s_turismo/ocupacion_hotelera/Base70centros.csv` | Mensual | E1, E2, E3 |
| 2 | **Banco de México – API SIE** ([documentación](https://www.banxico.org.mx/SieAPIRest/service/v1/)) | `SF43718`, tipo de cambio FIX en pesos por dólar (diario); `SP1`, INPC general (mensual). | API REST en JSON con token personal | Diaria / mensual | Covariables E1 (SARIMAX) y E2 (ANCOVA) |

### 4.2 Análisis ético y legal

| Criterio | Fuente 1: DataTur (datos.gob.mx / repodatos) | Fuente 2: Banxico SIE |
|---|---|---|
| **robots.txt** | `datos.gob.mx/robots.txt` sólo prohíbe `/dataset/rate/`, `/revision/`, `/dataset/*/history` y `/api/`, y pide `Crawl-Delay: 10`. La ficha del dataset está permitida y no usamos `/api/`. `repodatos.atdt.gob.mx/robots.txt` responde HTTP 403; según el estándar RFC 9309, un 4xx significa "no disponible" y no prohíbe el acceso. | `banxico.org.mx/robots.txt` prohíbe `/dyn/` y `/ALEPH`. La ruta usada, `/SieAPIRest/service/v1/`, no está restringida, y es la vía oficial que Banxico ofrece para consultar series de forma automatizada. |
| **Términos de uso y licencia** | **Creative Commons Atribución 4.0 (CC-BY 4.0)**, declarada en la ficha del dataset: permite copiar, redistribuir y transformar los datos, incluso con fines comerciales, citando a SECTUR como fuente. | El uso del API requiere un token personal y está sujeto a la "Salvedad de uso del API" publicada en la página del SIE. Los datos son información pública; se cita a Banco de México como fuente. Límites: 200 consultas cada 5 minutos y 10,000 al día para datos históricos. Usamos 2 consultas por ejecución. |
| **Datos personales** | No hay: son agregados estadísticos por destino. | No hay: indicadores macroeconómicos. |
| **Carga al servidor** | 1 petición por ejecución (archivo de unos 2.7 MB), como máximo una vez por semana. | 2 peticiones por ejecución. |
| **Identificación del cliente** | User-Agent propio: `ObservatorioTurismoColima/0.1 (proyecto academico; +https://github.com/Chonitoo/observatorio-turismo)`. | El mismo, más el token en el encabezado `Bmx-Token`. |
| **Manejo de credenciales** | No aplica. | El token se guarda como *secret* cifrado de GitHub (`BANXICO_TOKEN`); nunca se escribe en el código ni en la bitácora. |
| **Bloqueos** | El servidor rechaza peticiones automatizadas desde fuera de México (HTTP 403). **No se evade el bloqueo:** no se cambia el User-Agent, no se usan proxies y no se reintenta. El rechazo se registra en la bitácora y la serie histórica se obtuvo con una descarga manual legítima desde un navegador en México (documentada con su huella SHA-256). | No aplica. |

### 4.3 Arquitectura de captura (capa Bronce)

```
GitHub Actions (cron: día 5 de cada mes + lunes)
        │
        ▼
src/captura.py ──► src/extractores/datatur.py ─┐
                └─► src/extractores/banxico.py ─┤  1. lee robots.txt y respeta Crawl-delay
                                                │  2. descarga UNA vez, con User-Agent honesto
                                                │  3. si 401/403/429 → registra y NO evade
                                                │  4. SHA-256: si no cambió, no se duplica
                                                ▼
data/bronze/<fuente>/<nombre>_<fecha UTC>.<ext>   (crudo, inmutable)
data/bronze/_bitacora_captura.csv                 (trazabilidad de cada intento)
        │
        ▼
commit automático al repositorio (captura-bot)
```

La serie histórica inicial (108 meses) está en `data/bronze/datatur/Base70centros_2026-11-10_manual.csv`, con SHA-256 `a8ca3f9b…d7d671`. Una prueba automática verifica en cada ejecución que el archivo no se haya modificado y que tenga al menos 36 periodos para Manzanillo y para Colima.

### 4.4 Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| DataTur bloquea al runner de GitHub (servidores fuera de México). | Se registra el bloqueo sin evadirlo. Las actualizaciones se descargan manualmente desde México, se registran en la bitácora con su hash y Banxico sigue capturándose de forma automática. |
| SECTUR revisa cifras históricas hacia atrás. | Cada versión se guarda como un archivo nuevo e inmutable, así que se pueden comparar versiones en la capa Plata. |
| El rezago de publicación deja la serie en 2024-12. | Los 108 periodos bastan para E1 a E3. Se busca una actualización en DataTur (compendio estadístico y reportes mensuales) para la entrega E1. |
| Cambio de URL o de formato. | Las pruebas de columnas esperadas fallan y alertan en la corrida de Actions. |
