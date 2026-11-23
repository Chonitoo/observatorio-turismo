# Declaración de ética y legalidad de los datos

**Observatorio de Ocupación Hotelera de Colima (OOH-Colima)** · Maximiliano Encarnación Velázquez Rodríguez
Versión E2 · noviembre 2026 · Aplica a todas las fuentes, capas y productos del repositorio.

---

## 1. Principios

1. **Legalidad.** Sólo se usan fuentes públicas cuya licencia o términos permiten el uso académico y la
   redistribución, citando a su autor.
2. **Respeto a los servidores.** Antes de cada descarga se consulta `robots.txt` (RFC 9309). El cliente se identifica
   con un User-Agent propio, hace una petición por recurso, respeta `Crawl-delay` y los límites publicados.
   **Ningún bloqueo se evade**: no se cambia de User-Agent, no se usan proxies y no se reintenta de forma agresiva.
3. **Privacidad por diseño.** El observatorio trabaja con agregados estadísticos y establecimientos económicos, no
   con personas. Cualquier campo que pueda identificar a una persona física se descarta al leer Bronce.
4. **Trazabilidad.** Todo dato publicado en la capa Oro se puede rastrear hasta el archivo crudo, la fila y la fecha
   de ingesta (`data/gold/linaje_oro.csv`). Ningún registro inválido se borra en silencio: va a `data/quarantine/`
   con su motivo.
5. **Transparencia sobre sesgos.** Las limitaciones de cada fuente se documentan (sección 6) y se reflejan en cómo
   se interpretan los resultados.

## 2. Inventario de fuentes

| # | Fuente | Recurso | Acceso | Licencia / términos | Datos personales | Carga sobre el servidor |
|---|---|---|---|---|---|---|
| 1 | **SECTUR – DataTur**, ocupación hotelera de 70 destinos | `repodatos.atdt.gob.mx/s_turismo/ocupacion_hotelera/Base70centros.csv` (ficha en datos.gob.mx) | descarga pública | **CC-BY 4.0** | No (agregados por destino y categoría) | 1 petición por corrida |
| 2 | **Banco de México – API SIE**: FIX (`SF43718`) e INPC (`SP1`) | `banxico.org.mx/SieAPIRest/service/v1/series/...` | API REST con token personal | Salvedad de uso del API SIE; información pública con cita | No (indicadores nacionales) | 2 consultas por corrida (límite: 10,000 al día) |
| 3 | **INEGI – DENUE** Colima (descarga masiva) | `inegi.org.mx/contenidos/masiva/denue/denue_06_csv.zip` | descarga pública | **Términos de Libre Uso de la Información del INEGI** | **Sí, potencialmente** (nombre, razón social, teléfono, correo, domicilio) → **se descartan** | 1 petición por corrida (~3.8 MB); se deduplica por SHA-256 |
| 4 | **INEGI – Marco Geoestadístico**, municipios de Colima | `gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06` | servicio web público (GeoJSON) | **Términos de Libre Uso de la Información del INEGI** | No (polígonos y población total del Censo 2020) | 1 petición por corrida (~0.5 MB) |
| 5 | **Entrevista de campo** (E0) | llamada telefónica, 10/11/2026 | consentimiento verbal informado | uso académico | Sólo iniciales y puesto, con consentimiento | — |

### Fuente evaluada y descartada

| Fuente | Motivo del descarte |
|---|---|
| **OpenStreetMap vía Overpass API** (`overpass-api.de`) | Su `robots.txt` declara `Disallow: /api/` para todo agente, y `openstreetmap.org/robots.txt` pide expresamente no hacer *scraping* y usar las descargas masivas. Como el extractor respeta robots.txt, se descartó. Alternativa legítima para el futuro: los extractos masivos de OSM (licencia ODbL) en planet.openstreetmap.org o Geofabrik. |

## 3. Análisis de robots.txt

La revisión es **automática**: `src/comun.py::revisar_robots()` se ejecuta antes de cada descarga y queda registrada
en la columna `robots` de `data/bronze/_bitacora_captura.csv`.

| Servidor | Contenido relevante de robots.txt | Ruta usada | Resultado |
|---|---|---|---|
| `datos.gob.mx` | `Disallow: /dataset/rate/`, `/revision/`, `/dataset/*/history`, `/api/`; `Crawl-Delay: 10` | ficha del dataset (consulta manual) | Permitido; no se usa `/api/` |
| `repodatos.atdt.gob.mx` | Responde **HTTP 403** (también al robots.txt) | `/s_turismo/ocupacion_hotelera/Base70centros.csv` | robots 4xx = "no disponible" (RFC 9309). El servidor **bloquea clientes automatizados fuera de México**: se registra `bloqueado` y **no se evade**. La serie se obtuvo con una descarga manual legítima desde un navegador en México (SHA-256 documentado) |
| `www.banxico.org.mx` | `Disallow: /dyn/`, `/ALEPH` | `/SieAPIRest/service/v1/` | Permitido; es el canal oficial para consultas automatizadas |
| `www.inegi.org.mx` | `Allow: /app`, `/contenidos/...`; `Disallow: /auth/register/` y diccionarios con parámetros | `/contenidos/masiva/denue/` | Permitido |
| `gaia.inegi.org.mx` | No publica robots.txt (**HTTP 404**) | `/wscatgeo/v2/geo/mgem/06` | Permitido (RFC 9309: 4xx = sin restricciones) |
| `overpass-api.de` | `Disallow: /api/` | — | **Prohibido → fuente descartada** |

## 4. Términos de uso, licencias y atribución

| Fuente | Qué permite | Obligaciones que cumple el observatorio |
|---|---|---|
| DataTur (CC-BY 4.0) | Copiar, redistribuir, transformar, incluso con fines comerciales | Citar a SECTUR como fuente; indicar que los datos fueron transformados |
| Banxico SIE | Consultar y reutilizar las series públicas mediante el API con token | Token personal guardado como *secret* cifrado de GitHub (`BANXICO_TOKEN`), nunca en el código ni en la bitácora; respetar los límites (200 consultas cada 5 min); citar a Banco de México |
| INEGI (DENUE y Marco Geoestadístico) | Copiar, distribuir, publicar, adaptar, extraer y explotar comercialmente | (a) Citar "Fuente: INEGI, *producto*" y su fecha de actualización; (b) **avisar de las transformaciones** realizadas; (c) **no sugerir** que el análisis lo hizo o lo avala el INEGI |

**Citas que usa el observatorio:**

- Fuente: SECTUR, DataTur. *Ocupación hotelera en los 70 destinos principales monitoreados*. datos.gob.mx, CC-BY 4.0.
- Fuente: Banco de México, Sistema de Información Económica (SIE): series SF43718 y SP1.
- Fuente: INEGI, Directorio Estadístico Nacional de Unidades Económicas (DENUE) 05/2026.
- Fuente: INEGI, Marco Geoestadístico, diciembre de 2025; Censo de Población y Vivienda 2020.

**Aviso de transformación (INEGI):** los productos de este repositorio son **elaboración propia**. Se filtró el DENUE
a SCIAN 721 (alojamiento temporal), se descartaron columnas de identificación, se unió cada establecimiento a un
municipio por ubicación (GeoPandas) y se calcularon agregados y densidades. Nada de esto representa una postura
oficial del INEGI ni implica su aval. El mismo aviso aparece en los mapas.

## 5. Privacidad y protección de datos personales

- **Agregados, no personas.** DataTur, Banxico y el Marco Geoestadístico no contienen datos personales.
- **Minimización en DENUE.** DENUE publica datos de contacto de los negocios. En establecimientos pequeños (pensiones,
  casas de huéspedes, departamentos), el nombre o la razón social pueden ser el **nombre de una persona física**. El
  análisis no los necesita, así que `src/pipeline/geo.py` descarta al leer Bronce estas 15 columnas:
  `nom_estab, raz_social, telefono, correoelec, www, tipo_vial, nom_vial, numero_ext, numero_int, letra_ext,
  letra_int, edificio, edificio_e, nomb_asent, manzana`. Una prueba automática
  (`tests/test_e2_linaje_geo.py::test_privacidad_sin_columnas_personales`) falla si alguna llega a Plata u Oro.
- **El crudo se conserva sin modificar** en Bronce por trazabilidad. Ya es información pública del INEGI y no se
  publica en ningún producto derivado.
- **Coordenadas.** Se conservan las del establecimiento comercial, ya publicadas por INEGI. Los mapas muestran tipo y
  tamaño, nunca nombres.
- **Entrevista de campo.** Se identifica al entrevistado sólo con iniciales y puesto, con su consentimiento informado
  para uso académico.
- **Credenciales.** El token de Banxico vive sólo como *secret* de GitHub Actions; `.gitignore` excluye `.env` y `*.token`.
- **Marco legal.** El tratamiento se ajusta a la legislación mexicana de protección de datos personales en posesión de
  particulares (LFPDPPP): el observatorio no recaba ni trata datos personales identificables en sus productos.

## 6. Sesgos identificados y mitigación

| # | Sesgo | Evidencia en los datos | Mitigación |
|---|---|---|---|
| S1 | **Cobertura de DataTur**: sólo 70 destinos y hoteles de categoría turística; deja fuera Airbnb y el hospedaje informal | El entrevistado señaló que la renta vacacional absorbió las estancias largas en Manzanillo | No se generalizan los resultados a "todo el hospedaje". DENUE agrega departamentos, casas y cabañas para mostrar la oferta fuera de DataTur |
| S2 | **No respuesta creciente** (los hoteles reportan voluntariamente) | Los meses faltantes de 1★ pasan de 11 % a 21 % y los de 2★ de 4 % a 11 % después de 2020 | Diagnóstico de mecanismo (MCAR rechazado); los huecos estructurales (MNAR) no se imputan; `pct_oferta_imputada` y `registros_imputados` quedan visibles en Oro |
| S3 | **Actualización desigual de DENUE** | Los metadatos de INEGI indican que se actualiza "fundamentalmente" en establecimientos grandes | Los conteos de micronegocios se interpretan como aproximados |
| S4 | **`fecha_alta` no es fecha de apertura** | Pico artificial en 2010 (levantamiento que originó el DENUE) | No se usa para medir aperturas |
| S5 | **Supervivencia**: DENUE sólo lista negocios activos | — | No se infieren tendencias históricas de la oferta con DENUE |
| S6 | **Geocodificación** | 1 establecimiento declara Villa de Álvarez pero su punto cae en Colima | Se marca `municipio_coincide` y se usa el municipio espacial; los puntos a más de 1 km de Colima van a cuarentena (regla G-R2) |
| S7 | **Desfase temporal** entre fuentes | DENUE 2026, DataTur hasta 2024, población del Censo 2020 | Cada tabla declara su fecha; los cruces (cuartos por establecimiento) se presentan como aproximaciones |
| S8 | **Tratamiento de atípicos** que podría borrar eventos reales | Pandemia y huracán Otis | Los choques conocidos se conservan y se marcan; sólo se winsoriza el 2.5 % sin explicación, en una columna aparte |
| S9 | **Falacia ecológica** | Indicadores municipales | Los resultados describen municipios y destinos, no hoteles individuales |
| S10 | **Sesgo del analista** en umbrales (Baja/Media/Alta, temporadas) | — | Los umbrales están en `config.py`, justificados con la entrevista y modificables |

## 7. Uso responsable de los resultados

- El observatorio es un **ejercicio académico**. Sus pronósticos y comparaciones son apoyo para decidir, no
  información oficial.
- No se publican rankings de establecimientos individuales ni información que permita señalar a un negocio en
  particular.
- **Uso de IA:** se usó un asistente de IA (Claude Code) para apoyar la programación y la redacción. Las decisiones,
  la entrevista y la responsabilidad del contenido son del autor.

## 8. Lista de verificación

| Control | Dónde se verifica |
|---|---|
| robots.txt consultado antes de cada descarga | `src/comun.py`, columna `robots` de la bitácora |
| Ningún bloqueo evadido | estado `bloqueado` en la bitácora (DataTur) |
| Licencias citadas y aviso de transformación | sección 4, mapas, README |
| Sin datos personales en Plata/Oro | prueba automática de privacidad |
| Credenciales fuera del código | *secret* `BANXICO_TOKEN`, `.gitignore` |
| Registros inválidos en cuarentena con motivo | `data/quarantine/` |
| Linaje completo Oro → Bronce | `reports/E2/linaje.json` (`integro: true`, 0 registros sin linaje) |
