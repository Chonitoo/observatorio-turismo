"""Valores faltantes: diagnóstico del mecanismo (MCAR / MAR / MNAR) e imputación.

Hay dos tipos de faltante en DataTur:

1. **Explícitos**: celdas vacías dentro de un registro existente (NaN).
2. **Implícitos**: combinaciones centro × categoría × mes que no aparecen en el archivo.
   Se detectan construyendo la rejilla completa de periodos para cada serie que existe.

Diagnóstico
-----------
* Bajo MCAR la probabilidad de faltar no depende de ninguna variable. Se prueba con
  ji-cuadrada de independencia entre el indicador "falta" y variables observadas
  (año, categoría, tipo de centro). Si alguna es significativa, se rechaza MCAR.
* Si la ausencia se explica por variables observadas, el mecanismo es MAR y la imputación
  condicionada en esas variables (misma serie, meses vecinos) es válida.
* Huecos largos o al inicio/final de una serie corresponden a una categoría que no operaba
  o dejó de monitorearse: la ausencia depende del propio valor no observado (no había oferta).
  Se trata como MNAR / ausencia estructural y NO se imputa (imputar inventaría oferta hotelera).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config as C
from .calidad import CONTEOS

TASAS = {  # numerador: denominador (las tasas son estables y se interpolan mejor que los conteos)
    "cuartos_ocupados_residentes": "cuartos_disponibles",
    "cuartos_ocupados_no_residentes": "cuartos_disponibles",
    "llegada_turistas_residentes": "cuartos_ocupados_residentes",
    "llegada_turistas_no_residentes": "cuartos_ocupados_no_residentes",
    "turistas_noche_residentes": "llegada_turistas_residentes",
    "turistas_noche_no_residentes": "llegada_turistas_no_residentes",
}


def _periodo(df: pd.DataFrame) -> pd.Series:
    return pd.PeriodIndex.from_fields(year=df["anio"].astype(int), month=df["mes"].astype(int), freq="M")


def rejilla(df: pd.DataFrame) -> pd.DataFrame:
    """Rejilla completa centro × categoría × periodo con indicador de ausencia."""
    per = pd.period_range(C.PERIODO_INICIO, C.PERIODO_FIN, freq="M")
    pares = df[["centro", "categoria"]].drop_duplicates()
    g = pares.merge(pd.DataFrame({"periodo": per}), how="cross")
    obs = df.assign(periodo=_periodo(df))[["centro", "categoria", "periodo"]].assign(presente=True)
    g = g.merge(obs, how="left", on=["centro", "categoria", "periodo"])
    g["falta"] = g["presente"].isna()
    g["tipo_centro"] = g["centro"].map(df.drop_duplicates("centro").set_index("centro")["tipo_centro"])
    g["anio"] = g["periodo"].dt.year
    return g.drop(columns="presente")


def clasificar_huecos(g: pd.DataFrame) -> pd.DataFrame:
    """Etiqueta cada hueco como 'interno_corto' (imputable) o 'estructural'."""
    g = g.sort_values(["centro", "categoria", "periodo"]).copy()
    g["tipo_hueco"] = pd.NA
    for _, s in g.groupby(["centro", "categoria"], sort=False):
        falta = s["falta"].to_numpy()
        idx = s.index.to_numpy()
        n, i = len(falta), 0
        while i < n:
            if not falta[i]:
                i += 1
                continue
            j = i
            while j < n and falta[j]:
                j += 1
            interno = i > 0 and j < n
            etiqueta = "interno_corto" if interno and (j - i) <= C.HUECO_MAX_IMPUTABLE else "estructural"
            g.loc[idx[i:j], "tipo_hueco"] = etiqueta
            g.loc[idx[i:j], "largo_hueco"] = j - i
            i = j
    return g


def diagnostico(df: pd.DataFrame) -> dict:
    """Resumen del mecanismo de faltantes (se guarda en reports/E1/faltantes.json)."""
    explicitos = {c: int(n) for c, n in df[CONTEOS].isna().sum().items() if n}
    detalle_explicitos = (
        df[df[CONTEOS].isna().any(axis=1)][["anio", "mes", "centro", "categoria"]]
        .to_dict(orient="records")
    )
    g = clasificar_huecos(rejilla(df))
    pruebas = {}
    for var in ["anio", "categoria", "tipo_centro"]:
        tabla = pd.crosstab(g[var], g["falta"])
        chi2, p, gl, _ = stats.chi2_contingency(tabla)
        n = tabla.to_numpy().sum()
        v_cramer = float(np.sqrt(chi2 / (n * (min(tabla.shape) - 1))))
        pruebas[var] = {"chi2": round(float(chi2), 2), "gl": int(gl), "p_valor": float(p),
                        "v_cramer": round(v_cramer, 3),
                        "tasa_falta_por_nivel": g.groupby(var)["falta"].mean().round(4)
                        .rename(index=str).to_dict()}
    mcar_rechazado = any(v["p_valor"] < 0.05 for v in pruebas.values())
    huecos = g[g["falta"]]
    return {
        "faltantes_explicitos": explicitos,
        "detalle_explicitos": detalle_explicitos,
        "rejilla_esperada": int(len(g)),
        "faltantes_implicitos": int(g["falta"].sum()),
        "pct_implicitos": round(100 * g["falta"].mean(), 2),
        "pruebas_independencia": pruebas,
        "mcar_rechazado": mcar_rechazado,
        "huecos_por_tipo": huecos["tipo_hueco"].value_counts().to_dict(),
        "conclusion": (
            "Se rechaza MCAR: la ausencia depende de la categoría (sobre todo 1★ y 'Sin categoría'), "
            "del año (crece después de 2020) y del tipo de centro (más en ciudades). "
            "Huecos internos de hasta 3 meses se tratan como MAR y se imputan dentro de su serie; "
            "huecos largos o en los extremos son ausencia estructural (MNAR: la categoría no operaba "
            "o salió del monitoreo) y no se imputan."
        ) if mcar_rechazado else "No se rechaza MCAR.",
    }


def imputar_explicitos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Imputa conteos nulos por razón: valor = denominador × razón mediana de la misma serie
    en una ventana de ±6 meses (MAR condicionado a centro, categoría y tiempo)."""
    df = df.copy()
    df["periodo"] = _periodo(df)
    df["imputado"] = df.get("imputado", False)
    registro = []
    for col in [c for c in TASAS if df[c].isna().any()]:
        den = TASAS[col]
        for i in df.index[df[col].isna()]:
            r = df.loc[i]
            vecinos = df[(df.centro == r.centro) & (df.categoria == r.categoria)
                         & ((df.periodo - r.periodo).apply(lambda x: abs(x.n)) <= 6)
                         & df[col].notna() & (df[den] > 0)]
            razon = float((vecinos[col] / vecinos[den]).median())
            valor = float(np.round(r[den] * razon)) if r[den] > 0 else 0.0
            df.loc[i, col] = valor
            df.loc[i, "imputado"] = True
            registro.append({"centro": r.centro, "categoria": r.categoria, "periodo": str(r.periodo),
                             "columna": col, "metodo": f"razón mediana {col}/{den} ±6 meses",
                             "razon": round(razon, 4), "valor_imputado": valor})
    return df.drop(columns="periodo"), registro


def imputar_huecos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Crea los registros de huecos internos cortos interpolando linealmente en el tiempo
    la oferta (cuartos disponibles) y las tasas de cada serie; los conteos se reconstruyen."""
    g = clasificar_huecos(rejilla(df))
    objetivo = g[g["tipo_hueco"] == "interno_corto"]
    if objetivo.empty:
        return df, objetivo
    base = df.assign(periodo=_periodo(df))
    nuevos = []
    for (centro, cat), huecos in objetivo.groupby(["centro", "categoria"]):
        s = base[(base.centro == centro) & (base.categoria == cat)].set_index("periodo").sort_index()
        full = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
        t = full.index.to_timestamp()
        disp = full["cuartos_disponibles"].set_axis(t).interpolate("time")
        tasas = {num: (full[num] / full[den].replace(0, np.nan)).set_axis(t).interpolate("time").fillna(0)
                 for num, den in TASAS.items()}
        for per in huecos["periodo"]:
            ts = per.to_timestamp()
            fila = {"archivo_origen": "imputado", "fila_origen": pd.NA,
                    "anio": per.year, "mes": per.month, "centro": centro, "categoria": cat,
                    "tipo_centro": s["tipo_centro"].iloc[0], "subtipo_centro": s["subtipo_centro"].iloc[0],
                    "cuartos_disponibles": float(round(disp[ts]))}
            for num in ["cuartos_ocupados_residentes", "cuartos_ocupados_no_residentes",
                        "llegada_turistas_residentes", "llegada_turistas_no_residentes",
                        "turistas_noche_residentes", "turistas_noche_no_residentes"]:
                fila[num] = float(round(fila[TASAS[num]] * tasas[num][ts]))
            # garantizar consistencia lógica tras el redondeo
            for res in ["residentes", "no_residentes"]:
                fila[f"turistas_noche_{res}"] = max(fila[f"turistas_noche_{res}"], fila[f"llegada_turistas_{res}"])
            fila["imputado"] = True
            nuevos.append(fila)
    imputados = pd.DataFrame(nuevos)
    salida = pd.concat([df, imputados], ignore_index=True)
    salida["imputado"] = salida["imputado"].fillna(False).astype(bool)
    return salida, imputados
