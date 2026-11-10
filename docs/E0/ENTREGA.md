# Ficha de entrega técnica — E0

| Campo | Valor |
|---|---|
| Proyecto | Observatorio de Ocupación Hotelera de Colima (OOH-Colima) |
| Integrante | Maximiliano Encarnación Velázquez Rodríguez (`@Chonitoo`), trabajo individual |
| Repositorio | https://github.com/Chonitoo/observatorio-turismo |
| Tag | `e0` |
| Sector / región | Turismo, alojamiento (SCIAN 721) / Colima: Manzanillo y Colima capital |

## Lista de entregables

| # | Entregable | Ubicación | Estado |
|---|---|---|---|
| 1 | Propuesta del observatorio (ficha, entrevista, 3 preguntas analíticas, plan de datos con análisis ético y legal) | [`docs/E0/propuesta.md`](propuesta.md) | ✅ (completa) |
| 2a | Extractor ético automático (GitHub Actions) | [`.github/workflows/captura.yml`](../../.github/workflows/captura.yml), [`src/`](../../src) | ✅ |
| 2b | Serie histórica cruda con al menos 36 periodos | [`data/bronze/datatur/`](../../data/bronze/datatur): 108 meses (2016-01 a 2024-12) | ✅ |
| 3a | Bitácoras PSP | [`calidad/tiempo-maximiliano.csv`](../../calidad/tiempo-maximiliano.csv), [`calidad/defectos-maximiliano.csv`](../../calidad/defectos-maximiliano.csv) | ✅ |
| 3b | 3 objetivos de calidad medibles | [`calidad/README.md`](../../calidad/README.md) | ✅ |
| 4 | Ficha de entrega técnica | este archivo | ✅ |

## Cómo reproducir

```bash
git clone https://github.com/Chonitoo/observatorio-turismo.git
cd observatorio-turismo
pip install -r requirements.txt
python -m pytest -q                      # integridad de Bronce (5 pruebas)
export BANXICO_TOKEN=<tu_token>          # opcional; en Actions es un secret
python -m src.captura                    # ejecuta los extractores
```

## Máquina de captura

- **Programación:** el día 5 de cada mes y cada lunes a las 14:00 UTC, más ejecución manual (`workflow_dispatch`).
- **Fuentes:** DataTur, CSV CC-BY 4.0 · Banxico SIE: `SF43718` (tipo de cambio FIX) y `SP1` (INPC).
- **Ética:** consulta robots.txt (RFC 9309), respeta Crawl-delay, usa un User-Agent identificable, hace una petición por recurso y **no evade bloqueos** (un 401, 403 o 429 se registra como `bloqueado`).
- **Trazabilidad:** cada intento queda en `data/bronze/_bitacora_captura.csv` con su HTTP, bytes y SHA-256; los crudos son inmutables, se nombran con la fecha UTC y no se duplican si el hash no cambia.
- **Secret requerido:** `BANXICO_TOKEN` en *Settings → Secrets and variables → Actions*.

### Evidencia de funcionamiento

Primera corrida automática: [Captura Bronce #1](https://github.com/Chonitoo/observatorio-turismo/actions/runs/42911657807) (2026-11-10, ✅ success). Commit generado por el bot: `bronce: captura automática 2026-11-10T22:08Z`.

| Fuente | Estado | Contenido capturado |
|---|---|---|
| DataTur | `bloqueado` (HTTP 403), registrado sin evasión | Se conserva la serie semilla: 108 meses, 2016-01 a 2024-12 |
| Banxico `SF43718` (tipo de cambio FIX) | `nuevo` (HTTP 200) | 2,731 observaciones diarias, 2016-01-04 a 2026-11-10 |
| Banxico `SP1` (INPC) | `nuevo` (HTTP 200) | 130 meses, 2016-01 a 2026-10 |

## Estado conocido y limitaciones

- `repodatos.atdt.gob.mx` responde **403** a clientes automatizados fuera de México, incluido el runner de GitHub. La serie histórica se obtuvo con una descarga manual legítima desde un navegador en México (SHA-256 `a8ca3f9bf34edf46321a45c1abcd3f774363d02db0395f1d6132b8a7c4d7d671`). Los intentos automáticos siguen registrándose sin evadir el bloqueo.
- La serie DataTur publicada llega hasta 2024-12.

## Uso de herramientas de IA

Se usó un asistente de IA (Claude Code) como apoyo para estructurar el repositorio, escribir los extractores y redactar borradores. El autor revisó, validó y es responsable del contenido. La entrevista de campo es trabajo propio del autor.
