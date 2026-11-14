"""Detección y tratamiento de atípicos y ruido.

La ocupación hotelera tiene **tendencia** (destinos que crecen o decaen) y **estacionalidad**
(julio siempre está más lleno que septiembre). Detectar atípicos sobre el valor crudo marcaría
cada temporada alta como "atípica". Por eso primero se descompone cada serie (por destino):

    valor = tendencia + estacionalidad + residuo
    tendencia       = mediana móvil centrada de 13 meses (robusta a picos aislados)
    estacionalidad  = mediana, por mes calendario, del valor sin tendencia (excluye choques)
    residuo         = lo que queda; sobre él se buscan atípicos

Métodos sobre el residuo (umbrales estimados sólo con meses "normales" del destino):

* **IQR (Tukey)**: atípico si cae fuera de [Q1 − 1.5·IQR, Q3 + 1.5·IQR].
* **Z-Score robusto** (Iglewicz & Hoaglin, 1993): z = 0.6745·(x − mediana)/MAD; atípico si |z| > 3.5.
  Usa mediana y MAD, que no se distorsionan por los propios atípicos (a diferencia de media y DE).
* **Isolation Forest** (multivariado, opcional): se ejecuta si scikit-learn está disponible.

Un registro es atípico por **consenso** si lo marcan IQR y Z robusto a la vez.

Tratamiento
-----------
* Atípicos dentro de un **choque conocido** (pandemia COVID-19, huracán Otis en Acapulco) son reales:
  se conservan y se marcan con `choque_covid` / `evento_conocido` para modelarlos como intervención.
* Atípicos **sin explicación**: se *winsoriza* el residuo a la cerca IQR en `<var>_tratada`
  (valor = tendencia + estacionalidad + residuo recortado). El valor original se conserva en `<var>`.
* **Ruido**: `<var>_suavizada` = mediana móvil centrada de 3 meses (suavizamiento por vecindad).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def z_robusto(x: pd.Series, ref: pd.Series | None = None) -> pd.Series:
    ref = x if ref is None else ref
    med = ref.median()
    mad = (ref - med).abs().median()
    if mad == 0 or np.isnan(mad):
        return pd.Series(0.0, index=x.index)
    return 0.6745 * (x - med) / mad


def cercas_iqr(x: pd.Series, k: float = C.IQR_K) -> tuple[float, float]:
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def marcar_choques(df: pd.DataFrame) -> pd.DataFrame:
    df["choque_covid"] = df["periodo"].isin(C.MESES_COVID).astype(int)
    df["evento_conocido"] = ""
    df.loc[df["choque_covid"] == 1, "evento_conocido"] = "Pandemia COVID-19"
    for centro, (ini, fin, desc) in C.EVENTOS_CONOCIDOS.items():
        m = (df["centro"] == centro) & (df["periodo"] >= ini) & (df["periodo"] <= fin)
        df.loc[m, "evento_conocido"] = desc
    return df


def descomponer(s: pd.Series, mes: pd.Series, normal: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    # La tendencia se estima sin los meses de choque (si no, la caída de 2020 "jala" la tendencia
    # y los meses previos parecen atípicamente altos); en esos meses se interpola.
    base = s.where(normal)
    tendencia = (base.rolling(C.VENTANA_TENDENCIA, center=True, min_periods=5).median()
                 .interpolate(limit_direction="both"))
    sin_tend = s - tendencia
    estacional = sin_tend[normal].groupby(mes[normal]).median()
    est = mes.map(estacional).fillna(0)
    return tendencia, est, sin_tend - est


def detectar(df: pd.DataFrame, variables: list[str]) -> tuple[pd.DataFrame, dict]:
    df = marcar_choques(df.sort_values(["centro", "periodo"]).copy())
    choque = df["evento_conocido"] != ""
    resumen = {}
    for var in variables:
        cols = {k: pd.Series(np.nan, index=df.index) for k in ["esperado", "res", "lo", "hi", "z"]}
        for _, g in df.groupby("centro"):
            normal = ~choque.loc[g.index] & g[var].notna()
            tend, est, res = descomponer(g[var], g["mes"], normal)
            ref = res[normal].dropna()
            lo, hi = cercas_iqr(ref) if len(ref) > 8 else (-np.inf, np.inf)
            cols["esperado"].loc[g.index] = tend + est
            cols["res"].loc[g.index] = res
            cols["lo"].loc[g.index] = lo
            cols["hi"].loc[g.index] = hi
            cols["z"].loc[g.index] = z_robusto(res, ref) if len(ref) > 8 else 0.0
        res, lo, hi, z = cols["res"], cols["lo"], cols["hi"], cols["z"]
        df[f"atipico_iqr_{var}"] = ((res < lo) | (res > hi)).fillna(False)
        df[f"z_robusto_{var}"] = z.round(3)
        df[f"atipico_z_{var}"] = (z.abs() > C.Z_ROBUSTO_UMBRAL).fillna(False)
        consenso = df[f"atipico_iqr_{var}"] & df[f"atipico_z_{var}"]
        df[f"atipico_{var}"] = consenso
        winsor = consenso & ~choque
        df[f"{var}_tratada"] = np.where(winsor, cols["esperado"] + res.clip(lo, hi), df[var]).round(4)
        df[f"{var}_suavizada"] = (df.groupby("centro")[var]
                                  .transform(lambda s: s.rolling(3, center=True, min_periods=1).median()))
        resumen[var] = {
            "iqr": int(df[f"atipico_iqr_{var}"].sum()),
            "z_robusto": int(df[f"atipico_z_{var}"].sum()),
            "consenso": int(consenso.sum()),
            "consenso_en_choque_conocido": int((consenso & choque).sum()),
            "winsorizados": int(winsor.sum()),
            "pct_winsorizado": round(100 * winsor.mean(), 2),
            "ejemplos_winsorizados": df.loc[winsor, ["centro", "periodo", var, f"{var}_tratada"]]
            .round(2).head(15).to_dict(orient="records"),
            "ejemplos_choque": df.loc[consenso & choque, ["centro", "periodo", var, "evento_conocido"]]
            .round(2).head(10).to_dict(orient="records"),
        }

    # Isolation Forest (opcional, multivariado)
    try:
        from sklearn.ensemble import IsolationForest
        cols_if = variables + ["densidad", "pct_no_residentes"]
        X = df[cols_if].to_numpy(dtype=float)
        X = (X - np.nanmedian(X, axis=0)) / np.nanstd(X, axis=0)
        iso = IsolationForest(n_estimators=300, contamination=0.01, random_state=42)
        df["atipico_iforest"] = iso.fit_predict(np.nan_to_num(X)) == -1
        resumen["isolation_forest"] = {"disponible": True, "atipicos": int(df["atipico_iforest"].sum()),
                                       "en_choque_conocido": int((df["atipico_iforest"] & choque).sum()),
                                       "contaminacion": 0.01, "variables": cols_if}
    except Exception as e:  # p. ej. scikit-learn bloqueado por políticas del sistema operativo
        df["atipico_iforest"] = pd.NA
        resumen["isolation_forest"] = {"disponible": False, "motivo": f"{type(e).__name__}: {str(e)[:80]}"}
    return df, resumen
