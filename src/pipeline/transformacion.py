"""Jerarquías conceptuales, discretización, normalización y reducción de datos."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

CONTINUAS = ["ocupacion_pct", "estadia_promedio", "densidad", "pct_no_residentes",
             "cuartos_disponibles", "llegadas", "tipo_cambio", "inflacion_anual_pct"]


# --- Jerarquías conceptuales -------------------------------------------------
def periodo_covid(anio: pd.Series, mes: pd.Series) -> pd.Series:
    p = anio * 100 + mes
    return pd.Series(np.select([p < 202003, p <= 202112], ["Prepandemia", "Pandemia"], "Pospandemia"),
                     index=anio.index)


def agregar_jerarquias(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    anio, mes = d["anio"].astype(int), d["mes"].astype(int)
    # Tiempo: mes → trimestre → semestre → año ; mes → temporada ; año → periodo COVID
    d["trimestre"] = anio.astype(str) + "-T" + ((mes - 1) // 3 + 1).astype(str)
    d["semestre"] = anio.astype(str) + "-S" + ((mes - 1) // 6 + 1).astype(str)
    d["temporada"] = mes.map(C.MES_TEMPORADA)
    d["periodo_covid"] = periodo_covid(anio, mes)
    # Espacio: centro → entidad → región Banxico → país ; centro → subtipo → tipo
    d["estado"] = d["centro"].map(C.CENTRO_ESTADO)
    d["region"] = d["estado"].map(C.ESTADO_REGION)
    d["pais"] = "México"
    d["litoral"] = np.where(d["tipo_centro"] != "Centros de Playa", "No aplica",
                            np.where(d["centro"].isin(C.LITORAL_GOLFO_CARIBE), "Golfo-Caribe", "Pacífico"))
    grupo = {c: g for g, cs in C.GRUPOS_E3.items() for c in cs}
    d["grupo_e3"] = d["centro"].map(grupo).fillna("Otro")
    if "categoria" in d:
        d["segmento"] = d["categoria"].map(C.CATEGORIA_SEGMENTO)
    return d


# --- Discretización ----------------------------------------------------------
def discretizar(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # 1) Por umbrales de negocio (ancho definido por el sector): Baja <40, Media 40-60, Alta >=60
    d["ocupacion_nivel"] = pd.cut(d["ocupacion_pct"], C.OCUPACION_CORTES, labels=C.OCUPACION_ETIQUETAS,
                                  right=False).astype(str)
    # 2) Por igual frecuencia (quintiles): cada clase tiene ~20 % de los registros
    d["ocupacion_quintil"] = pd.qcut(d["ocupacion_pct"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"]).astype(str)
    # 3) Estadía por igual ancho
    d["estadia_clase"] = pd.cut(d["estadia_promedio"], [1, 1.5, 2, 3, 30],
                                labels=["Exprés (<1.5)", "Corta (1.5-2)", "Media (2-3)", "Larga (3+)"],
                                right=False).astype(str).replace("nan", "Sin llegadas")
    # 4) Tipo de cambio por terciles (peso fuerte / medio / débil)
    d["tipo_cambio_tercil"] = pd.qcut(d["tipo_cambio"], 3, labels=["Peso fuerte", "Medio", "Peso débil"]
                                      ).astype(str)
    return d


# --- Normalización -----------------------------------------------------------
def normalizar(df: pd.DataFrame, columnas=CONTINUAS) -> tuple[pd.DataFrame, dict]:
    """Min-Max a [0, 1] y Z-Score (media 0, DE 1). Los parámetros se guardan para poder
    aplicar exactamente la misma transformación a datos nuevos (o revertirla)."""
    d = df.copy()
    params = {}
    for c in columnas:
        x = d[c].astype(float)
        mn, mx, mu, sd = x.min(), x.max(), x.mean(), x.std(ddof=0)
        d[f"{c}_minmax"] = ((x - mn) / (mx - mn)).round(6)
        d[f"{c}_z"] = ((x - mu) / sd).round(6)
        params[c] = {"min": float(mn), "max": float(mx), "media": float(mu), "desv_est": float(sd)}
    return d, params


# --- Reducción ---------------------------------------------------------------
def seleccion_variables(df: pd.DataFrame, columnas=CONTINUAS, umbral: float = 0.95) -> dict:
    """Selección por correlación: de cada par con |r| > umbral se descarta la variable
    con mayor correlación media con el resto (redundante)."""
    corr = df[columnas].corr().abs()
    descartar = set()
    pares = []
    for i, a in enumerate(columnas):
        for b in columnas[i + 1:]:
            if corr.loc[a, b] > umbral and a not in descartar and b not in descartar:
                quitar = a if corr[a].mean() > corr[b].mean() else b
                descartar.add(quitar)
                pares.append({"a": a, "b": b, "r": round(float(corr.loc[a, b]), 3), "descartada": quitar})
    return {"umbral": umbral, "pares_redundantes": pares, "descartadas": sorted(descartar),
            "seleccionadas": [c for c in columnas if c not in descartar],
            "matriz_correlacion": corr.round(3).to_dict()}
