"""Fuentes 3 y 4: INEGI — información geoespacial.

Fuente 3 · DENUE (Directorio Estadístico Nacional de Unidades Económicas), descarga masiva de Colima.
  Recurso:    https://www.inegi.org.mx/contenidos/masiva/denue/denue_06_csv.zip
  Contenido:  establecimientos activos con actividad SCIAN, tamaño (personal ocupado),
              municipio, coordenadas y fecha de alta. Se usan sólo los de hospedaje (SCIAN 721).
  Licencia:   Términos de Libre Uso de la Información del INEGI.
  Frecuencia: anual (la descarga semanal sólo registra "sin_cambios" mientras no se actualice).

Fuente 4 · Marco Geoestadístico (límites municipales de Colima), servicio web wscatgeo de INEGI.
  Recurso:    https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06   (GeoJSON, 10 municipios)
  Contenido:  polígonos municipales + población del Censo de Población y Vivienda 2020.
  Licencia:   Términos de Libre Uso de la Información del INEGI.

Ambas son descargas públicas sin autenticación. robots.txt de www.inegi.org.mx no prohíbe
/contenidos/masiva/ y gaia.inegi.org.mx no publica robots.txt (HTTP 404 => permitido, RFC 9309).
"""
from src.comun import ResultadoCaptura, descargar_crudo

DENUE_URL = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_06_csv.zip"
MG_URL = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06"


def capturar() -> list[ResultadoCaptura]:
    return [
        descargar_crudo("inegi_denue_colima", DENUE_URL, "denue_06_csv", "zip"),
        descargar_crudo("inegi_mg_municipios", MG_URL, "mgem_06_colima", "geojson"),
    ]


if __name__ == "__main__":
    for r in capturar():
        print(r)
