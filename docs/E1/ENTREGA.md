# Ficha de entrega técnica — E1

| Campo | Valor |
|---|---|
| Proyecto | Observatorio de Ocupación Hotelera de Colima (OOH-Colima) |
| Integrante | Maximiliano Encarnación Velázquez Rodríguez (`@Chonitoo`), trabajo individual |
| Repositorio | https://github.com/Chonitoo/observatorio-turismo |
| Tag | `e1` |
| Objetivo | Automatizar el flujo Bronce → Plata → Oro con limpieza estadística y una Puerta de Calidad con cuarentena |

## Lista de entregables

| # | Requisito | Dónde está | Evidencia |
|---|---|---|---|
| 1a | Faltantes: diagnóstico MCAR/MAR/MNAR e imputación justificada | `src/pipeline/faltantes.py` · notebook §3 | `reports/E1/faltantes.json` |
| 1b | Atípicos y ruido (IQR + Z-Score robusto; Isolation Forest de contraste) | `src/pipeline/atipicos.py` · notebook §5 | `reports/E1/atipicos.json`, `docs/E1/img/atipicos_manzanillo.png` |
| 1c | Normalización Min-Max y Z-Score | `src/pipeline/transformacion.py` · notebook §6 | `data/gold/parametros_normalizacion.json` |
| 1d | Discretización y jerarquías conceptuales | `src/pipeline/transformacion.py`, `config.py` · notebook §7 | columnas `ocupacion_nivel`, `temporada`, `region`, `segmento`… |
| 1e | Reducción (agregación, selección de variables y de casos) | `src/pipeline/integracion.py`, `transformacion.py` · notebook §8 | `reports/E1/integracion_reduccion.json` |
| 2 | Integración DataTur + Banxico con resolución de conflictos | `src/pipeline/integracion.py`, `bronce.py` · notebook §4 | `data/gold/destino_mes.csv` |
| 3 | Puerta de Calidad (Pandera) con cuarentena documentada | `src/pipeline/calidad.py` · notebook §2 | `data/quarantine/*.csv`, `reports/E1/calidad.json` |
| 4 | Notebook explicativo ejecutado | [`docs/E1/limpieza.ipynb`](limpieza.ipynb) | 6 figuras en `docs/E1/img/` |
| 5 | Ficha técnica y relatoría | este archivo · [`docs/relatoria-E1.md`](../relatoria-E1.md) | |

## Arquitectura

```
data/bronze/  (crudo, inmutable)
   │  bronce.py: localiza el último crudo por la bitácora y estandariza nombres y tipos
   ▼
[Puerta 1 · entrada] ── inválidos ──► data/quarantine/
   │  faltantes.py: diagnóstico + imputación explícita (razón) + huecos internos ≤ 3 meses (interpolación)
   ▼
[Puerta 2 · Plata]   ── inválidos ──► data/quarantine/
   ▼
data/silver/  datatur_hoteles.csv · banxico_tipo_cambio.csv · banxico_inpc.csv
   │  integracion.py: FIX diario→mensual, INPC→inflación anual, agregación centro×mes, unión por periodo
   │  atipicos.py: tendencia + estacionalidad + residuo → IQR ∧ Z robusto → winsoriza sólo atípicos no explicados
   │  transformacion.py: jerarquías, discretización, Min-Max, Z-Score, selección de variables
   ▼
[Puerta 3 · Oro]     ── inválidos ──► data/quarantine/
   ▼
data/gold/    destino_mes.csv · hotel_categoria_mes.csv · serie_colima.csv · parametros_normalizacion.json
```

**Automatización:** el workflow `.github/workflows/captura.yml` ejecuta, en cada corrida programada (día 5 de cada
mes y cada lunes) o manual: pruebas → captura Bronce → `python -m src.pipeline.ejecutar` → commit de todas las capas.

## Resultados de la corrida

| Puerta | Fuente | Entrada | Válidos | Cuarentena | Motivos |
|---|---|---:|---:|---:|---|
| 1 · entrada | DataTur | 31,147 | 31,141 | 6 | R1 ocupados > disponibles (2); R2 ocupados sin llegadas (4) |
| 1 · entrada | Banxico FIX | 2,731 | 2,731 | 0 | |
| 1 · entrada | Banxico INPC | 130 | 130 | 0 | |
| 2 · Plata | DataTur (incluye 147 imputados) | 31,288 | 31,287 | 1 | R2 en un registro imputado (la puerta también valida la imputación) |
| 3 · Oro | destino × mes | 6,900 | 6,898 | 2 | estadía > 30 noches (Nuevo Nayarit, abr y may 2020) |

En todas las puertas se cumple **válidos + cuarentena = entrada**: ningún registro se elimina en silencio.

| Salida | Registros |
|---|---:|
| `data/silver/datatur_hoteles.csv` | 31,287 |
| `data/gold/destino_mes.csv` | 6,898 (64 destinos × 108 meses, menos huecos y cuarentena) |
| `data/gold/hotel_categoria_mes.csv` (para E2) | 31,287 |
| `data/gold/serie_colima.csv` (para el pronóstico) | 216 (Manzanillo y Colima × 108 meses) |

## Decisiones principales

| Tema | Decisión | Justificación |
|---|---|---|
| Mecanismo de faltantes | No es MCAR (χ² con año, categoría y tipo de centro, p < 10⁻³⁰) | La ausencia depende de variables observadas |
| Huecos internos ≤ 3 meses | Imputar (147) por interpolación de oferta y tasas | MAR: la serie vecina explica el valor |
| Huecos largos o en los extremos | No imputar (2,300) | MNAR/estructural: la categoría no operaba; imputar inventaría oferta |
| Nulo explícito (1) | Razón mediana ±6 meses | Conserva la estadía típica de esa serie |
| Atípicos | Consenso IQR ∧ Z robusto sobre el residuo | Sin la estacionalidad, cada verano sería "atípico" |
| Choques reales (COVID, Otis) | Conservar y marcar | Son información; se modelarán como intervención |
| Atípicos sin explicación | Winsorizar (2.5 %) en columna aparte | El original no se pierde |
| Normalización | Min-Max y Z-Score con parámetros guardados | Reproducible y reversible |
| Regiones | Regionalización de Banxico | Fuente oficial y consistente con la otra fuente |

## Cómo reproducir

```bash
pip install -r requirements.txt
python -m pytest -q                          # 19 pruebas (Bronce + pipeline)
python -m src.pipeline.ejecutar              # Bronce → Plata → Oro (≈ 6 s)
python -m nbconvert --to notebook --execute --inplace docs/E1/limpieza.ipynb
```

## Limitaciones conocidas

- **Inflación 2016 nula:** la captura de Banxico arrancaba en 2016-01 y la variación anual necesita 12 meses
  previos. El extractor ya se corrigió para iniciar en 2015-01; la siguiente corrida automática completa el dato.
- **Semana Santa:** cambia entre marzo y abril, y genera algunos atípicos "sin explicación" en esos meses. Se
  agregará una variable indicadora en la siguiente entrega.
- **Isolation Forest** depende de scikit-learn. Si el sistema operativo bloquea la librería, el pipeline sigue
  funcionando con IQR y Z robusto, y registra el motivo en `atipicos.json`.
- DataTur sigue bloqueando la descarga automática desde fuera de México (ver E0), así que el pipeline usa la
  última versión cruda registrada en la bitácora.

## Uso de herramientas de IA

Se usó un asistente de IA (Claude Code) para apoyar la escritura del código, las pruebas y los borradores de la
documentación. El autor revisó las decisiones metodológicas y los resultados, y es responsable del contenido.
