# Ficha de entrega técnica — E2

| Campo | Valor |
|---|---|
| Proyecto | Observatorio de Ocupación Hotelera de Colima (OOH-Colima) |
| Integrante | Maximiliano Encarnación Velázquez Rodríguez (`@Chonitoo`), trabajo individual |
| Repositorio | https://github.com/Chonitoo/observatorio-turismo |
| Tag | `e2` |
| Objetivo | Integrar una fuente avanzada, garantizar trazabilidad completa y declarar ética y legalidad |

## Lista de entregables

| # | Requisito | Dónde está | Evidencia |
|---|---|---|---|
| 1 | **Fuente especializada geoespacial**: DENUE (INEGI) + Marco Geoestadístico con GeoPandas y cartografía | `src/extractores/inegi.py`, `src/pipeline/geo.py` · notebook §1–3 | `docs/E2/img/mapa_hospedaje_colima.png`, `mapa_manzanillo.png`, mapa interactivo `docs/E2/mapa_hospedaje_colima.html` |
| 2 | **Declaración de ética y legalidad** | [`docs/etica-datos.md`](../etica-datos.md) | términos, robots.txt, licencias, privacidad, 10 sesgos con mitigación |
| 3 | **Linaje y trazabilidad** Oro → Bronce con fecha de ingesta | `src/pipeline/bronce.py`, `src/pipeline/linaje.py` · notebook §4 | `data/gold/linaje_oro.csv`, `reports/E2/linaje.json` |
| 4 | Notebook ejecutado | [`docs/E2/geoespacial_linaje.ipynb`](geoespacial_linaje.ipynb) | 4 figuras + mapa interactivo |
| 5 | Ficha y relatoría | este archivo · [`docs/relatoria-E2.md`](../relatoria-E2.md) | |

## 1. Fuente geoespacial

| Fuente | Recurso | Contenido | Licencia |
|---|---|---|---|
| DENUE 05/2026 (INEGI) | `inegi.org.mx/contenidos/masiva/denue/denue_06_csv.zip` | 42,073 establecimientos de Colima; se usan los **294 de hospedaje (SCIAN 721)** con coordenadas, tipo, tamaño y fecha de alta | Términos de Libre Uso del INEGI |
| Marco Geoestadístico dic-2025 (INEGI) | `gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06` | 10 polígonos municipales + población del Censo 2020 | Términos de Libre Uso del INEGI |

**Procesamiento (GeoPandas):**
1. Minimización: se descartan 15 columnas que pueden identificar personas.
2. Puerta G1 (Pandera): SCIAN, estrato de personal, entidad, municipio, coordenadas, fecha e id único.
3. Unión espacial punto → municipio (`sjoin_nearest`, EPSG:6372) y bandera `municipio_coincide`.
4. Puerta G2: el punto debe estar a menos de 1 km de Colima.
5. Agregación municipal: establecimientos por tipo y tamaño, empleo estimado, densidad por 10 mil habitantes y por
   100 km², y cruce con los cuartos de DataTur.

**Salidas:** `data/silver/denue_hospedaje_colima.csv`, `data/silver/municipios_colima.geojson`,
`data/gold/establecimientos_hospedaje.csv`, `data/gold/municipio_hospedaje.csv`.

**Hallazgos principales:**

| Municipio | Establecimientos | % del estado | Por 10 mil hab. | Cuartos DataTur 2024 | Cuartos por establecimiento |
|---|---:|---:|---:|---:|---:|
| Manzanillo | 134 | 45.6 | 7.0 | 4,313 | ≈ 32 |
| Colima | 54 | 18.4 | 3.4 | 1,164 | ≈ 22 |
| Tecomán | 46 | 15.6 | 4.0 | — | — |
| Armería | 27 | 9.2 | **9.8** | — | — |

- 73 % de los establecimientos son micro (0–10 personas); los 4 grandes (251+ personas) están en Manzanillo, que concentra el 63 % del empleo estimado del sector.
- Villa de Álvarez, segundo municipio más poblado, sólo tiene 5: su demanda se aloja en Colima capital.

**Fuente descartada:** OpenStreetMap/Overpass, porque `overpass-api.de/robots.txt` prohíbe `/api/` (ver
`etica-datos.md`).

## 2. Linaje y trazabilidad

**Cómo funciona.** Desde la lectura de Bronce, cada registro recibe `id_bronce`
(`<fuente>:<sha256[:10]>:<fila>`), `archivo_origen`, `fila_origen`, `sha256_bronce` y `fecha_ingesta` (tomada de la
bitácora de captura). Esas columnas viajan a Plata. En Oro cada registro tiene `id_oro`, y la tabla larga
`data/gold/linaje_oro.csv` enumera todos los registros crudos que lo produjeron y el **rol** de cada uno:

| Rol | Filas |
|---|---:|
| agregación centro×categoría→centro (DataTur) | 31,135 |
| base de imputación (registros reales que rodean un hueco imputado) | 292 |
| promedio mensual del FIX diario (Banxico) | 2,264 |
| INPC del mes / INPC 12 meses antes | 108 + 108 |
| registro DENUE / conteo por unión espacial | 294 + 294 |
| polígono, área y población (Marco Geoestadístico) | 10 |
| **Total** | **34,505** |

**Resultado de la verificación** (`reports/E2/linaje.json`): **7,310 registros de Oro**, todos con linaje (0 sin
origen), 5 archivos de Bronce, huellas SHA-256 coincidentes con la bitácora, `integro: true`. El pipeline **se
detiene** si algún registro de Oro queda sin linaje.

**Rastrear cualquier registro:**

```python
from src.pipeline import linaje
linaje.rastrear("Manzanillo|2024-07")   # filas crudas de DataTur + días del FIX + INPC, con fecha de ingesta
linaje.rastrear("municipio|06007")      # establecimientos DENUE y polígono del Marco Geoestadístico
linaje.verificar()                      # integridad completa del linaje
```

Además, `destino_mes.csv` incluye columnas de linaje resumido (`linaje_datatur`, `linaje_tipo_cambio`, `linaje_inpc`,
`fecha_ingesta_*`) y `hotel_categoria_mes.csv` lleva el `id_bronce` de cada fila.

## 3. Evidencia de ejecución automática

Corrida [Captura Bronce y pipeline #4](https://github.com/Chonitoo/observatorio-turismo/actions/runs/45102579874)
(2026-11-23, ✅ success), commit del bot `datos: captura y pipeline automáticos 2026-11-23T02:52Z`:

| Fuente | Resultado en GitHub Actions |
|---|---|
| INEGI DENUE | HTTP 200 · `sin_cambios` (misma huella SHA-256: no se duplica) |
| INEGI Marco Geoestadístico | HTTP 200 · `sin_cambios` |
| Banxico FIX / INPC | HTTP 200 · `nuevo` / `sin_cambios` |
| DataTur | HTTP 403 · `bloqueado` (registrado sin evasión, como desde E0) |
| Linaje | 7,310 / 7,310 registros de Oro rastreables, `integro: true` |

## 4. Calidad

| Puerta | Fuente | Entrada | Válidos | Cuarentena |
|---|---|---:|---:|---:|
| G1 · entrada | DENUE hospedaje | 294 | 294 | 0 |
| G2 · Plata | DENUE con unión espacial | 294 | 294 | 0 |
| 1–3 (E1) | DataTur / Banxico / Oro | ver `reports/E1/calidad.json` | | 9 |

## Cómo reproducir

```bash
pip install -r requirements.txt
python -m src.captura                 # Bronce: DataTur, Banxico, DENUE, Marco Geoestadístico
python -m src.pipeline.ejecutar       # Plata/Oro + rama geoespacial + linaje (falla si el linaje está incompleto)
python -m pytest -q                   # 21 pruebas (incluye linaje y privacidad)
python -m nbconvert --to notebook --execute --inplace docs/E2/geoespacial_linaje.ipynb
```

## Limitaciones

- DENUE se actualiza sobre todo en establecimientos grandes; los conteos de micronegocios son aproximados.
- La razón cuartos/establecimiento cruza DataTur (hoteles de categoría turística, 2024) con DENUE (todo el
  alojamiento, 2026): es indicativa.
- La captura semanal de DENUE registrará `sin_cambios` hasta que INEGI publique la siguiente versión.

## Uso de herramientas de IA

Se usó un asistente de IA (Claude Code) para apoyar la programación y los borradores de la documentación. El autor
revisó las decisiones y es responsable del contenido.
