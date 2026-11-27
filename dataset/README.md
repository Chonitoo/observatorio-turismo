# Observatorio de Ocupación Hotelera de Colima — dataset curado

**Versión 1.0.0** · Licencia **CC BY 4.0** · Generado automáticamente desde la capa Oro del observatorio.

| Archivo | Filas | Columnas | Contenido |
|---|---:|---:|---|
| `ocupacion_destino_mes.csv` | 6,900 | 31 | Ocupación hotelera mensual por destino turístico (64 destinos, 2016-2024), integrada con tipo de cambio e inflación. |
| `ocupacion_categoria_mes.csv` | 31,265 | 16 | Ocupación hotelera mensual por destino y categoría (1★-5★), para análisis de factores. |
| `hospedaje_establecimientos.csv` | 294 | 16 | Establecimientos de hospedaje de Colima (DENUE 2026) con ubicación, tipo y tamaño. Sin datos de contacto. |
| `hospedaje_municipios.csv` | 10 | 17 | Oferta de hospedaje por municipio de Colima con densidades por población y superficie. |
| `indicadores_macro_mes.csv` | 143 | 6 | Tipo de cambio FIX e inflación anual (INPC) mensuales. |

- `parquet/`: las mismas tablas en formato Parquet (tipos preservados, más ligeras).
- `diccionario_datos.csv`: descripción, tipo y unidad de cada columna.
- `datapackage.json`: metadatos estándar ([Frictionless Data Package](https://datapackage.org/)).
- `SHA256SUMS.txt`: huellas para verificar la integridad de cada archivo.
- **Ficha técnica completa (datasheet):** [`docs/E3/datasheet.md`](https://github.com/Chonitoo/observatorio-turismo/blob/main/docs/E3/datasheet.md).

## Carga rápida

```python
import pandas as pd
base = "https://raw.githubusercontent.com/Chonitoo/observatorio-turismo/main/dataset/"
ocupacion = pd.read_csv(base + "ocupacion_destino_mes.csv")
```

## Cita

Maximiliano Encarnación Velázquez Rodríguez (2026). *Observatorio de Ocupación Hotelera de Colima — dataset curado* (v1.0.0). https://github.com/Chonitoo/observatorio-turismo
