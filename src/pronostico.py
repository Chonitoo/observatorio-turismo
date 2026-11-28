"""Pronóstico de la ocupación hotelera a 12 meses por destino (pregunta analítica E1 de la propuesta).

Uso:  python -m src.pronostico

Modelo
------
SARIMAX(1,0,1)(0,1,1)₁₂ sobre la ocupación mensual (%) de cada destino, con la variable indicadora
`choque_covid` como regresor exógeno (intervención): así la caída de 2020 no deforma la estacionalidad
ni el nivel pronosticado. Los meses faltantes se interpolan sólo para ajustar el modelo.

Validación
----------
Para cada destino se reserva el último año (12 meses), se ajusta con lo anterior y se compara contra el
método ingenuo estacional ("el mismo mes del año pasado"). Se reportan MAE y MAPE de ambos; el modelo
se usa si mejora al ingenuo, y si no, se publica el pronóstico ingenuo (con su banda empírica).

Salidas
-------
data/gold/pronostico_destino_mes.csv   destino × mes futuro: pronóstico, bandas 80 % y 95 %, método
reports/E4/pronostico_metricas.json    error de validación por destino y resumen
"""
from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.pipeline import config as C
from src.pipeline.io_rapido import escribir_csv

HORIZONTE = 12
MIN_MESES = 60
SALIDA = C.ORO / "pronostico_destino_mes.csv"
METRICAS = C.RAIZ / "reports" / "E4" / "pronostico_metricas.json"


def _serie(o: pd.DataFrame, centro: str) -> tuple[pd.Series, pd.Series]:
    d = o[o.centro == centro].copy()
    d.index = pd.PeriodIndex(d["periodo"], freq="M")
    idx = pd.period_range(d.index.min(), d.index.max(), freq="M")
    y = d["ocupacion_pct"].reindex(idx).interpolate(limit_direction="both")
    covid = pd.Series(idx.astype(str).isin(C.MESES_COVID).astype(float), index=idx)
    return y, covid


def _ajustar(y: pd.Series, covid: pd.Series, pasos: int):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = SARIMAX(y.to_timestamp(), exog=covid.to_timestamp().to_frame(), order=(1, 0, 1),
                    seasonal_order=(0, 1, 1, 12), enforce_stationarity=False, enforce_invertibility=False)
        r = m.fit(disp=False, maxiter=200)
        futuro = np.zeros((pasos, 1))
        f = r.get_forecast(pasos, exog=futuro)
    return f.predicted_mean.to_numpy(), f.conf_int(alpha=0.20).to_numpy(), f.conf_int(alpha=0.05).to_numpy()


def _ingenuo(y: pd.Series, pasos: int) -> np.ndarray:
    base = y[~y.index.astype(str).isin(C.MESES_COVID)]
    ultimo = base.iloc[-12:].to_numpy()
    return np.resize(ultimo, pasos)


def _errores(real: np.ndarray, pred: np.ndarray) -> dict:
    e = np.abs(real - pred)
    return {"mae": round(float(e.mean()), 2), "mape": round(float(100 * (e / np.maximum(real, 1)).mean()), 2)}


def pronosticar() -> dict:
    o = pd.read_csv(C.ORO / "destino_mes.csv", usecols=["centro", "periodo", "ocupacion_pct"])
    filas, metricas = [], {}
    for centro in sorted(o.centro.unique()):
        y, covid = _serie(o, centro)
        if len(y) < MIN_MESES:
            continue
        # --- validación: último año fuera de muestra
        ent, prueba = y.iloc[:-HORIZONTE], y.iloc[-HORIZONTE:]
        try:
            p_mod, _, _ = _ajustar(ent, covid.iloc[:-HORIZONTE], HORIZONTE)
            err_mod = _errores(prueba.to_numpy(), np.clip(p_mod, 0, 100))
        except Exception as e:  # noqa: BLE001 - un destino problemático no detiene a los demás
            err_mod = {"mae": np.inf, "mape": np.inf, "error": type(e).__name__}
        err_ing = _errores(prueba.to_numpy(), _ingenuo(ent, HORIZONTE))
        usar_modelo = err_mod["mae"] < err_ing["mae"]

        # --- pronóstico final con toda la serie
        futuro = pd.period_range(y.index.max() + 1, periods=HORIZONTE, freq="M")
        if usar_modelo:
            p, i80, i95 = _ajustar(y, covid, HORIZONTE)
            metodo = "SARIMAX(1,0,1)(0,1,1)12 + intervención COVID"
        else:
            p = _ingenuo(y, HORIZONTE)
            s = err_ing["mae"]   # banda empírica a partir del error de validación
            i80 = np.column_stack([p - 1.28 * s, p + 1.28 * s])
            i95 = np.column_stack([p - 1.96 * s, p + 1.96 * s])
            metodo = "Ingenuo estacional (mismo mes del año anterior)"
        for k, per in enumerate(futuro):
            filas.append({"centro": centro, "periodo": str(per), "anio": per.year, "mes": per.month,
                          "pronostico_pct": round(float(np.clip(p[k], 0, 100)), 2),
                          "li80": round(float(np.clip(i80[k, 0], 0, 100)), 2),
                          "ls80": round(float(np.clip(i80[k, 1], 0, 100)), 2),
                          "li95": round(float(np.clip(i95[k, 0], 0, 100)), 2),
                          "ls95": round(float(np.clip(i95[k, 1], 0, 100)), 2),
                          "metodo": metodo, "ultimo_dato": str(y.index.max())})
        metricas[centro] = {"modelo": err_mod, "ingenuo": err_ing, "metodo_publicado": metodo,
                            "meses_entrenamiento": int(len(y))}

    escribir_csv(pd.DataFrame(filas), SALIDA)
    usados = [m for m in metricas.values() if m["metodo_publicado"].startswith("SARIMAX")]
    mae_pub = [m["modelo"]["mae"] if m["metodo_publicado"].startswith("SARIMAX") else m["ingenuo"]["mae"]
               for m in metricas.values()]
    resumen = {
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "destinos": len(metricas), "horizonte_meses": HORIZONTE,
        "destinos_con_sarimax": len(usados),
        "mae_mediano_publicado_pts": round(float(np.median(mae_pub)), 2),
        "mae_mediano_ingenuo_pts": round(float(np.median([m["ingenuo"]["mae"] for m in metricas.values()])), 2),
        "por_destino": metricas,
    }
    METRICAS.parent.mkdir(parents=True, exist_ok=True)
    METRICAS.write_text(json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding="utf-8",
                        newline="\n")
    return resumen


if __name__ == "__main__":
    r = pronosticar()
    print({k: v for k, v in r.items() if k != "por_destino"})
    print("Manzanillo:", r["por_destino"].get("Manzanillo"))
