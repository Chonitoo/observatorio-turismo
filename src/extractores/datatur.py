"""Fuente 1: SECTUR / DataTur — Ocupación hotelera en los 70 destinos principales.

Ficha:      https://www.datos.gob.mx/dataset/ocupacion_hotelera_70_destinos_principales_monitoreados_datatur
Recurso:    https://repodatos.atdt.gob.mx/s_turismo/ocupacion_hotelera/Base70centros.csv
Licencia:   Creative Commons Attribution 4.0 (CC-BY 4.0)
Frecuencia: mensual, por destino (centro turístico) y categoría hotelera.
"""
from src.comun import ResultadoCaptura, descargar_crudo

FUENTE = "datatur"
URL = "https://repodatos.atdt.gob.mx/s_turismo/ocupacion_hotelera/Base70centros.csv"


def capturar() -> ResultadoCaptura:
    return descargar_crudo(FUENTE, URL, "Base70centros", "csv")


if __name__ == "__main__":
    print(capturar())
