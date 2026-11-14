"""Integración de fuentes heterogéneas y resolución de conflictos.

| Conflicto            | DataTur                         | Banxico FIX               | Banxico INPC          | Resolución                                  |
|----------------------|---------------------------------|---------------------------|-----------------------|---------------------------------------------|
| Formato              | CSV separado por tabuladores    | JSON anidado (bmx.series) | JSON anidado          | Ambos se llevan a DataFrame tabular         |
| Llave temporal       | `anio` (int) + `mes` (texto "01") | `fecha` texto dd/mm/aaaa | `fecha` día 1 del mes | Llave común `periodo` = "AAAA-MM"           |
| Tipo del valor       | enteros / float                 | texto ("17.3529", "N/E")  | texto                 | `to_numeric` + Puerta de Calidad            |
| Frecuencia           | mensual                         | **diaria** hábil          | mensual               | FIX → promedio mensual y cierre de mes      |
| Granularidad         | centro × categoría              | nacional                  | nacional              | DataTur se agrega a centro; Banxico se replica a todos los centros |
| Cobertura            | 2016-01 a 2024-12               | 2016-01 a hoy             | 2016-01 a hoy         | Unión izquierda sobre DataTur (variable objetivo) |
| Unidades             | cuartos-noche, personas         | pesos por dólar           | índice (2Q-jul-2018=100) | INPC → inflación anual % (variación a 12 meses) |
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def tipo_cambio_mensual(tc: pd.DataFrame) -> pd.DataFrame:
    t = tc.assign(periodo=tc["fecha"].dt.to_period("M").astype(str)).sort_values("fecha")
    return (t.groupby("periodo")
            .agg(tipo_cambio=("tipo_cambio", "mean"), tipo_cambio_cierre=("tipo_cambio", "last"),
                 dias_cotizados=("tipo_cambio", "size"))
            .round(4).reset_index())


def inflacion_mensual(inpc: pd.DataFrame) -> pd.DataFrame:
    i = inpc.assign(periodo=inpc["fecha"].dt.to_period("M").astype(str)).sort_values("periodo")
    i["inflacion_anual_pct"] = (i["inpc"].pct_change(12) * 100).round(3)
    return i[["periodo", "inpc", "inflacion_anual_pct"]]


def agregar_destino(plata: pd.DataFrame) -> pd.DataFrame:
    """Reducción por agregación: centro × categoría × mes → centro × mes."""
    d = plata.copy()
    d["periodo"] = (d["anio"].astype(int).astype(str) + "-" + d["mes"].astype(int).astype(str).str.zfill(2))
    d["ocupados"] = d["cuartos_ocupados_residentes"] + d["cuartos_ocupados_no_residentes"]
    d["llegadas"] = d["llegada_turistas_residentes"] + d["llegada_turistas_no_residentes"]
    d["noches"] = d["turistas_noche_residentes"] + d["turistas_noche_no_residentes"]
    d["disp_imputada"] = np.where(d["imputado"], d["cuartos_disponibles"], 0)
    g = (d.groupby(["periodo", "anio", "mes", "tipo_centro", "subtipo_centro", "centro"], as_index=False)
         .agg(cuartos_disponibles=("cuartos_disponibles", "sum"), cuartos_ocupados=("ocupados", "sum"),
              llegadas=("llegadas", "sum"), llegadas_no_residentes=("llegada_turistas_no_residentes", "sum"),
              turistas_noche=("noches", "sum"), categorias_reportadas=("categoria", "nunique"),
              disp_imputada=("disp_imputada", "sum")))
    g["ocupacion_pct"] = (100 * g["cuartos_ocupados"] / g["cuartos_disponibles"]).round(3)
    g["estadia_promedio"] = (g["turistas_noche"] / g["llegadas"]).round(4)
    g["densidad"] = (g["turistas_noche"] / g["cuartos_ocupados"]).round(4)
    g["pct_no_residentes"] = (100 * g["llegadas_no_residentes"] / g["llegadas"]).round(3)
    g["pct_oferta_imputada"] = (100 * g["disp_imputada"] / g["cuartos_disponibles"]).round(3)
    return g.drop(columns="disp_imputada")


def integrar(destino_mes: pd.DataFrame, tc_mes: pd.DataFrame, infl: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = destino_mes.merge(tc_mes, on="periodo", how="left").merge(infl, on="periodo", how="left")
    reporte = {
        "registros_datatur_destino_mes": int(len(destino_mes)),
        "registros_integrados": int(len(out)),
        "periodos_sin_tipo_cambio": sorted(out.loc[out["tipo_cambio"].isna(), "periodo"].unique().tolist()),
        "periodos_sin_inflacion": sorted(out.loc[out["inflacion_anual_pct"].isna(), "periodo"].unique().tolist()),
        "cobertura_banxico_fuera_de_datatur": sorted(set(tc_mes["periodo"]) - set(destino_mes["periodo"]))[:3]
        + ["..."],
    }
    return out, reporte
