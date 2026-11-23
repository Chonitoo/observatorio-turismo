# Observatorio de Ocupación Hotelera de Colima

[![Captura Bronce](https://github.com/Chonitoo/observatorio-turismo/actions/workflows/captura.yml/badge.svg)](https://github.com/Chonitoo/observatorio-turismo/actions/workflows/captura.yml)

> *¿Por qué los hoteles de Manzanillo llenan apenas la mitad de sus cuartos y cuánto ocuparán en los próximos 12 meses?*

Observatorio de datos del sector turístico de Colima: pronóstico de la ocupación (E1), análisis de factores (E2) y comparación multivariada con otros destinos del Pacífico (E3).

**Autor:** Maximiliano Encarnación Velázquez Rodríguez (`@Chonitoo`)

## Estructura

```
.github/workflows/captura.yml   Máquina de captura automática (GitHub Actions)
src/
  comun.py                      robots.txt, descarga ética, SHA-256, bitácora
  captura.py                    Orquestador
  extractores/datatur.py        SECTUR-DataTur: ocupación hotelera de 70 destinos (CC-BY 4.0)
  extractores/banxico.py        Banxico SIE: tipo de cambio FIX e INPC
  extractores/inegi.py          INEGI: DENUE (hospedaje) y Marco Geoestadístico (municipios)
  pipeline/                     Bronce → Plata → Oro: Puerta de Calidad (Pandera), faltantes,
                                atípicos, integración, jerarquías, normalización
data/bronze/                    Capa Bronce: datos crudos inmutables + _bitacora_captura.csv
data/silver/                    Capa Plata: datos limpios y validados
data/gold/                      Capa Oro: integrados y listos para analizar
data/quarantine/                Registros rechazados por la Puerta de Calidad, con motivo
reports/E1/                     Evidencia de cada etapa del pipeline (JSON)
docs/E0/, docs/E1/               Documentación de cada entrega
calidad/                        Bitácoras PSP de tiempo y defectos, objetivos de calidad
tests/                          Pruebas de integridad de Bronce
```

## Entregas

| Entrega | Tag | Documentos |
|---|---|---|
| E0: Arranque | `e0` | [Propuesta](docs/E0/propuesta.md) · [Ficha técnica](docs/E0/ENTREGA.md) |
| E1: Limpieza y Puerta de Calidad | `e1` | [Notebook](docs/E1/limpieza.ipynb) · [Ficha técnica](docs/E1/ENTREGA.md) · [Relatoría](docs/relatoria-E1.md) |
| E2: Fuente geoespacial, linaje y ética | `e2` | [Notebook](docs/E2/geoespacial_linaje.ipynb) · [Ficha técnica](docs/E2/ENTREGA.md) · [Relatoría](docs/relatoria-E2.md) · [Ética](docs/etica-datos.md) |

## Fuentes y licencias

Detalle completo en [docs/etica-datos.md](docs/etica-datos.md).

- SECTUR, DataTur: *Ocupación hotelera en los 70 destinos principales*, datos.gob.mx, licencia CC-BY 4.0.
- Banco de México: Sistema de Información Económica (SIE), API REST.
- Fuente: INEGI, DENUE 05/2026 y Marco Geoestadístico dic-2025 (Términos de Libre Uso de la Información del INEGI).
  Los productos derivados son elaboración propia y no representan una postura del INEGI.
