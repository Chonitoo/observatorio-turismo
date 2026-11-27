# Datasheet — Observatorio de Ocupación Hotelera de Colima (dataset curado v1.0.0)

Ficha técnica según el marco *Datasheets for Datasets* (Gebru et al., 2018/2021). Responde las preguntas que un
tercero necesita para decidir si este dataset le sirve, y cómo usarlo de forma responsable.

| Campo | Valor |
|---|---|
| Nombre | `observatorio-hotelero-colima` |
| Versión | 1.0.0 (noviembre 2026) |
| Ubicación | [`dataset/`](../../dataset) en https://github.com/Chonitoo/observatorio-turismo |
| Licencia | **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)** |
| Formato | CSV UTF-8 + Parquet; metadatos `datapackage.json` (Frictionless Data Package, validado) |
| Autor | Maximiliano Encarnación Velázquez Rodríguez |
| Cita | Velázquez Rodríguez, M. E. (2026). *Observatorio de Ocupación Hotelera de Colima — dataset curado* (v1.0.0). https://github.com/Chonitoo/observatorio-turismo |

---

## 1. Motivación

**¿Para qué se creó el dataset?**
Para responder una pregunta concreta del sector turístico de Colima: *¿por qué los hoteles de Manzanillo llenan
apenas la mitad de sus cuartos y cuánto ocuparán en los próximos meses?* Los datos oficiales existen, pero están
dispersos en tres instituciones, en formatos distintos (CSV con tabuladores, JSON, ZIP en latin-1), con huecos,
registros inconsistentes y sin una forma de rastrear el origen de cada cifra. Este dataset los entrega limpios,
integrados, validados y trazables.

**¿Quién lo creó y en qué contexto?**
Un estudiante de 7.º semestre, como proyecto integrador académico de las materias de
análisis y ciencia de datos. No representa a ninguna institución.

**¿Quién lo financió?**
Nadie: es un proyecto académico sin financiamiento.

## 2. Composición

**¿Qué representa cada instancia?** El dataset tiene cinco tablas:

| Tabla | Instancia (una fila =) | Filas | Columnas | Periodo |
|---|---|---:|---:|---|
| `ocupacion_destino_mes` | un destino turístico en un mes | 6,900 | 31 | 2016-01 a 2024-12 |
| `ocupacion_categoria_mes` | una categoría hotelera (1★–5★) de un destino en un mes | 31,265 | 16 | 2016-01 a 2024-12 |
| `hospedaje_establecimientos` | un establecimiento de hospedaje de Colima | 294 | 16 | DENUE 05/2026 |
| `hospedaje_municipios` | un municipio de Colima | 10 | 17 | DENUE 2026, Censo 2020 |
| `indicadores_macro_mes` | un mes (indicadores nacionales) | 143 | 6 | 2015-01 a 2026-11 |

El significado, tipo y unidad de cada columna están en [`dataset/diccionario_datos.csv`](../../dataset/diccionario_datos.csv)
y en el esquema del `datapackage.json`.

**¿Es una muestra o la población completa?**
- Ocupación: cubre los **64 destinos** con datos en el archivo de DataTur (el programa monitorea 70 centros turísticos).
  **No** es todo el hospedaje de México: sólo hoteles de categoría turística que reportan a SECTUR.
- Establecimientos: **todos** los establecimientos de alojamiento temporal (SCIAN 721) de Colima registrados en el
  DENUE, que se actualiza sobre todo en los establecimientos grandes.

**¿Hay etiquetas o variables objetivo?**
No hay etiquetas manuales. Las variables derivadas son: `ocupacion_nivel` (discretización), `atipico` (detección
estadística) y `evento_conocido` (choques documentados). La variable de interés para pronóstico es `ocupacion_pct`.

**¿Faltan datos?**
- **Huecos estructurales (no imputados):** 2,300 combinaciones destino × categoría × mes, porque la categoría no
  operaba o salió del monitoreo. Esas filas simplemente no existen en `ocupacion_categoria_mes`.
- **Imputados:** 127 registros (126 huecos internos de hasta 3 meses + 1 nulo explícito). Se marcan con
  `imputado = true` y, en la tabla por destino, con `registros_imputados` y `pct_oferta_imputada`.
- **Huecos en pandemia (no imputados):** 23 combinaciones en meses de choque COVID, porque los meses vecinos no
  representan ese periodo.
- **Razones vacías:** `estadia_promedio`, `densidad` y `pct_extranjeros` están vacías en 12 destino-mes con cero
  llegadas (cierres de 2020): la división es indefinida.
- **Indicadores:** la inflación anual falta en 2015 (no hay INPC de 2014 en la captura) y en el último mes si
  Banxico aún no publica el INPC.

**¿Hay errores, ruido o redundancias conocidas?**
- 8 registros crudos de DataTur se excluyeron por inconsistentes y están documentados en
  `data/quarantine/datatur_cuarentena.csv`, con su motivo:
  - R1, más cuartos ocupados que disponibles: 2 registros.
  - R2, ocupación sin llegadas: 4 registros.
  - R6, más de 30 noches por turista: 2 registros.
- 774 destino-mes están marcados como **atípicos**. La mayoría son reales, como la pandemia y el huracán Otis.
  `ocupacion_pct_tratada` sólo modifica los atípicos sin explicación (≈ 2.5 %).
- Los totales por destino son la suma de las categorías reportadas, así que si una categoría falta, la oferta del
  mes es menor.

**¿Es autocontenido?** Sí. Las fuentes originales están citadas, y el repositorio conserva los archivos crudos
(capa Bronce) con su huella SHA-256.

**¿Contiene datos confidenciales o personales?**
**No.** DataTur y Banxico son agregados estadísticos. Del DENUE se **eliminaron desde la lectura** el nombre del
establecimiento, la razón social, el teléfono, el correo, la página web y el domicilio, porque en negocios pequeños
pueden identificar a una persona física. Se conservan las coordenadas del establecimiento comercial (ya publicadas
por INEGI) y los identificadores `id_denue` y `clee`, que son públicos.

**¿Identifica subpoblaciones?** Agrupa por destino, estado, región, categoría hotelera y tipo y tamaño de
establecimiento. No contiene información sobre personas.

## 3. Proceso de recolección

**¿Cómo se obtuvieron los datos?**

| Fuente | Mecanismo | Frecuencia |
|---|---|---|
| SECTUR, DataTur (CC BY 4.0) | descarga del CSV `Base70centros.csv`. El servidor bloquea clientes automatizados fuera de México: la serie se descargó manualmente desde un navegador en México (10/11/2026); el bloqueo automático se registra y **no se evade** | mensual |
| Banco de México, API SIE | API REST con token personal (series SF43718 y SP1) | semanal (GitHub Actions) |
| INEGI, DENUE 05/2026 | descarga masiva pública `denue_06_csv.zip` | anual; se verifica cada semana por SHA-256 |
| INEGI, Marco Geoestadístico dic-2025 | servicio web wscatgeo (GeoJSON) | anual |

**¿Quién participó y cómo?** Un extractor automático que respeta `robots.txt` (RFC 9309), se identifica con un
User-Agent propio y registra cada intento en `data/bronze/_bitacora_captura.csv` (URL, HTTP, bytes, SHA-256, fecha).

**¿Cuándo?** La serie de ocupación cubre 2016–2024. Las capturas automáticas empezaron el 10/11/2026.

**¿Hubo revisión ética?** El proyecto tiene una declaración de ética y legalidad
([`docs/etica-datos.md`](../etica-datos.md)): términos de uso, robots.txt, licencias, privacidad y 10 sesgos con su
mitigación. No se recolectaron datos de personas. La única fuente primaria, una entrevista de campo, no forma parte
del dataset.

## 4. Preprocesamiento, limpieza y etiquetado

Los datos crudos (Bronce) pasan por un pipeline automático (`src/pipeline/`), y el dataset se genera desde la capa
Oro con `python -m src.publicar`:

1. **Puerta de Calidad 1 (Pandera):** se revisan el tipo, el dominio, el rango y la consistencia lógica:
   - R1: ocupados ≤ disponibles.
   - R2: si hay ocupación, debe haber llegadas.
   - R3: noches ≥ llegadas.
   - R4: densidad ≤ 6.
   - R5: la llave es única.
   - R6: estadía ≤ 30 noches.

   Los registros inválidos van a cuarentena con su motivo; nunca se borran en silencio.
2. **Faltantes:** diagnóstico del mecanismo. MCAR se rechaza con χ² (p < 10⁻³⁰). Después:
   - Huecos internos de hasta 3 meses: se imputan por interpolación de la oferta y las tasas (MAR).
   - Huecos largos o en los extremos: no se imputan (MNAR, estructurales).
   - Huecos en meses de pandemia: no se imputan.

   Cada registro imputado se valida con las reglas antes de emitirse.
3. **Puerta de Calidad 2** sobre los datos limpios, incluidos los imputados.
4. **Integración:**
   - DataTur se agrega de categoría a destino.
   - El tipo de cambio FIX pasa de diario a promedio mensual.
   - El INPC se convierte en inflación anual.
   - Todo se une con la llave común `periodo`.
5. **Atípicos:** cada serie se descompone en tendencia + estacionalidad + residuo, y se aplica el consenso IQR +
   Z-score robusto. Los choques conocidos se conservan; sólo se winsorizan los atípicos sin explicación, en una
   columna aparte.
6. **Transformaciones:**
   - Jerarquías: temporada, periodo COVID, región Banxico y segmento.
   - Discretización de la ocupación.
7. **Geoespacial:** unión espacial de cada establecimiento a su municipio (GeoPandas, EPSG:6372), con tolerancia
   costera de 1 km.
8. **Puerta de Calidad 3 (Oro)** y **validación de publicación:**
   - Pandera.
   - Control de que no haya columnas personales.
   - Validación Frictionless del `datapackage.json`.

**¿Se conservan los datos crudos?** Sí, en `data/bronze/`, inmutables y con su SHA-256. Cada fila del dataset tiene
`id_registro`, y `data/gold/linaje_oro.csv` lo conecta con el archivo, la fila y la fecha de ingesta de origen.

**¿El software está disponible?** Sí, en el mismo repositorio (`src/`), con 31 pruebas automáticas.

## 5. Usos

### Usos recomendados ✅
- **Pronóstico** de la ocupación hotelera mensual por destino (SARIMA/SARIMAX), usando `ocupacion_pct` y las
  variables exógenas `tipo_cambio`, `inflacion_anual_pct` y `evento_conocido`.
- **Análisis de factores** (ANOVA, diseño factorial observacional) con `ocupacion_categoria_mes`: tipo de destino ×
  categoría × temporada × periodo COVID.
- **Comparación multivariada** entre destinos de playa (PCA, MANOVA, clúster) con ocupación, estadía, densidad y %
  de extranjeros.
- **Planeación local:** estacionalidad por destino, tamaño de la oferta por municipio de Colima, temporadas bajas
  para promociones.
- **Docencia:** ejemplo completo de limpieza, imputación con diagnóstico, cuarentena y linaje.

### Usos NO recomendados ❌
- **Medir todo el hospedaje** de un destino: DataTur no incluye renta vacacional (Airbnb) ni hospedaje informal.
- **Evaluar o clasificar hoteles individuales:** los datos de ocupación son agregados por destino y categoría.
- **Usar `anio_alta` como año de apertura** de un negocio: es el año de registro en el DENUE (pico artificial en 2010).
- **Inferir tendencias de la oferta** con el DENUE: sólo lista negocios activos en 2026 (sesgo de supervivencia).
- **Tratar los valores imputados o winsorizados como observados:** filtra con `imputado` o usa `ocupacion_pct`
  en lugar de `ocupacion_pct_tratada` cuando necesites el dato original.
- **Presentarlo como estadística oficial** o sugerir que SECTUR, Banco de México o INEGI avalan el análisis.

**¿Hay riesgos de daño?** Bajos: no hay datos personales. El riesgo principal es la **interpretación**: conclusiones
sobre "todo el turismo" a partir de hoteles de categoría turística, o sobre un municipio a partir de agregados
(falacia ecológica).

## 6. Distribución

- **Dónde:** carpeta [`dataset/`](../../dataset) del repositorio público en GitHub, versión marcada con el tag `e3`.
  Para leerlo directo:
  `https://raw.githubusercontent.com/Chonitoo/observatorio-turismo/main/dataset/ocupacion_destino_mes.csv`
- **Licencia:** CC BY 4.0, con atribución a las fuentes originales (ver [`dataset/LICENSE.md`](../../dataset/LICENSE.md)).
- **Restricciones de terceros:** las de las fuentes originales, todas compatibles con la redistribución citando la
  fuente:
  - DataTur: CC BY 4.0.
  - INEGI: Términos de Libre Uso; piden citar la fuente, avisar de las transformaciones y no sugerir aval.
  - Banco de México: información pública, citando la fuente.
- **Integridad:** `SHA256SUMS.txt` y los `hash` del `datapackage.json` permiten verificar cada archivo.

## 7. Mantenimiento

- **Responsable:** el autor (`@Chonitoo` en GitHub). Errores y sugerencias: *Issues* del repositorio.
- **Actualización:** GitHub Actions captura, limpia, valida y **regenera el dataset cada lunes y cada día 5**. La
  ocupación se actualiza cuando SECTUR publica una nueva versión de DataTur; los indicadores de Banxico, cada semana.
- **Versionado:** versión semántica en `datapackage.json`. Cambios de esquema → versión mayor; datos nuevos con el
  mismo esquema → versión menor. Cada entrega queda congelada en un tag de git (`e3`, …).
- **Erratas:** las correcciones de reglas o imputación se documentan en las relatorías (`docs/relatoria-E*.md`) y
  se reflejan en `reports/`.
- **Contribuciones:** bienvenidas vía *pull request*. Toda fuente nueva debe pasar por el extractor ético y la
  Puerta de Calidad.

---

*Referencia del marco:* Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., &
Crawford, K. (2021). Datasheets for Datasets. *Communications of the ACM, 64*(12), 86–92.
