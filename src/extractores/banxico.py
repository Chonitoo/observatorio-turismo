"""Fuente 2: Banco de México — API del Sistema de Información Económica (SIE).

Documentación: https://www.banxico.org.mx/SieAPIRest/service/v1/
Límites:       200 consultas / 5 min y 10,000 / día para datos históricos (por token).
Autenticación: token personal de 64 caracteres, enviado en el encabezado `Bmx-Token`.
               Se lee de la variable de entorno BANXICO_TOKEN (secret de GitHub Actions);
               NUNCA se escribe en el código ni en la bitácora.

Series capturadas (factores explicativos para E2):
  SF43718  Tipo de cambio pesos por dólar E.U.A., FIX (diario)
  SP1      Índice Nacional de Precios al Consumidor (INPC, mensual)
"""
import os

from src.comun import ResultadoCaptura, descargar_crudo, registrar

FUENTE = "banxico"
SERIES = {
    "SF43718": "tipo_cambio_fix",
    "SP1": "inpc",
}
FECHA_INICIO = "2016-01-01"  # mismo arranque que la serie de DataTur
BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{ini}/{fin}"


def capturar(fecha_fin: str | None = None) -> list[ResultadoCaptura]:
    from datetime import date

    token = os.environ.get("BANXICO_TOKEN", "").strip()
    fin = fecha_fin or date.today().isoformat()
    resultados = []
    for serie, alias in SERIES.items():
        url = BASE.format(serie=serie, ini=FECHA_INICIO, fin=fin)
        if not token:
            res = ResultadoCaptura(f"{FUENTE}_{alias}", url, "-", None, "error",
                                   nota="Falta BANXICO_TOKEN (configurar secret)")
            registrar(res)
            resultados.append(res)
            continue
        resultados.append(
            descargar_crudo(
                f"{FUENTE}_{alias}", url, f"{serie}_{alias}", "json",
                headers={"Bmx-Token": token, "Accept": "application/json"},
            )
        )
    return resultados


if __name__ == "__main__":
    for r in capturar():
        print(r)
