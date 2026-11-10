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
data/bronze/                    Capa Bronce: datos crudos inmutables + _bitacora_captura.csv
docs/E0/                        propuesta.md y ENTREGA.md
calidad/                        Bitácoras PSP de tiempo y defectos, objetivos de calidad
tests/                          Pruebas de integridad de Bronce
```

## Entregas

| Entrega | Tag | Documentos |
|---|---|---|
| E0: Arranque | `e0` | [Propuesta](docs/E0/propuesta.md) · [Ficha técnica](docs/E0/ENTREGA.md) |

## Fuentes y licencias

- SECTUR, DataTur: *Ocupación hotelera en los 70 destinos principales*, datos.gob.mx, licencia CC-BY 4.0.
- Banco de México: Sistema de Información Económica (SIE), API REST.
