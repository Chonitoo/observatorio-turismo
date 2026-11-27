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
    m = (t.groupby("periodo")
         .agg(tipo_cambio=("tipo_cambio", "mean"), tipo_cambio_cierre=("tipo_cambio", "last"),
              dias_cotizados=("tipo_cambio", "size"), _ini=("fila_origen", "min"), _fin=("fila_origen", "max"),
              _arch=("archivo_origen", "first"), fecha_ingesta_tipo_cambio=("fecha_ingesta", "first"))
         .round(4).reset_index())
    # Linaje: los días del mes ocupan posiciones contiguas en bmx.series[0].datos del archivo crudo
    m["linaje_tipo_cambio"] = m["_arch"] + "#datos[" + m["_ini"].astype(str) + ":" + m["_fin"].astype(str) + "]"
    return m.drop(columns=["_ini", "_fin", "_arch"])


def inflacion_mensual(inpc: pd.DataFrame) -> pd.DataFrame:
    i = inpc.assign(periodo=inpc["fecha"].dt.to_period("M").astype(str)).sort_values("periodo")
    i["inflacion_anual_pct"] = (i["inpc"].pct_change(12) * 100).round(3)
    # Linaje: la inflación usa dos registros crudos (el mes y el mismo mes del año anterior)
    i["linaje_inpc"] = i["id_bronce"].shift(12).fillna("") + "|" + i["id_bronce"]
    i["fecha_ingesta_inpc"] = i["fecha_ingesta"]
    return i[["periodo", "inpc", "inflacion_anual_pct", "linaje_inpc", "fecha_ingesta_inpc"]]


def agregar_destino(plata: pd.DataFrame) -> pd.DataFrame:
    """Reducción por agregación: centro × categoría × mes → centro × mes."""
    d = plata.copy()
    d["periodo"] = (d["anio"].astype(int).astype(str) + "-" + d["mes"].astype(int).astype(str).str.zfill(2))
    d["ocupados"] = d["cuartos_ocupados_residentes"] + d["cuartos_ocupados_no_residentes"]
    d["llegadas"] = d["llegada_turistas_residentes"] + d["llegada_turistas_no_residentes"]
    d["noches"] = d["turistas_noche_residentes"] + d["turistas_noche_no_residentes"]
    d["disp_imputada"] = np.where(d["imputado"], d["cuartos_disponibles"], 0)
    # E3: se agrupa sólo por la llave (centro, periodo); los atributos del centro se recuperan
    # después. La lista de linaje se arma con ";".join sobre datos ya ordenados (sin lambda por grupo).
    d = d.sort_values(["centro", "periodo", "id_bronce"])
    llave = ["centro", "periodo"]
    grp = d.groupby(llave, sort=False)
    g = grp.agg(anio=("anio", "first"), mes=("mes", "first"), tipo_centro=("tipo_centro", "first"),
                subtipo_centro=("subtipo_centro", "first"),
                cuartos_disponibles=("cuartos_disponibles", "sum"), cuartos_ocupados=("ocupados", "sum"),
                llegadas=("llegadas", "sum"), llegadas_no_residentes=("llegada_turistas_no_residentes", "sum"),
                turistas_noche=("noches", "sum"), categorias_reportadas=("categoria", "nunique"),
                disp_imputada=("disp_imputada", "sum"), registros_imputados=("imputado", "sum"),
                fecha_ingesta_datatur=("fecha_ingesta", "max")).reset_index()
    g["linaje_datatur"] = grp["id_bronce"].agg(";".join).to_numpy()
    g = g[["periodo", "anio", "mes", "tipo_centro", "subtipo_centro", "centro", "cuartos_disponibles",
           "cuartos_ocupados", "llegadas", "llegadas_no_residentes", "turistas_noche", "categorias_reportadas",
           "disp_imputada", "registros_imputados", "linaje_datatur", "fecha_ingesta_datatur"]]
    g = g.sort_values(["periodo", "centro"]).reset_index(drop=True)
    g.insert(0, "id_oro", g["centro"] + "|" + g["periodo"])
    g["ocupacion_pct"] = (100 * g["cuartos_ocupados"] / g["cuartos_disponibles"]).round(3)
    g["estadia_promedio"] = (g["turistas_noche"] / g["llegadas"]).round(4)
    g["densidad"] = (g["turistas_noche"] / g["cuartos_ocupados"]).round(4)
    g["pct_no_residentes"] = (100 * g["llegadas_no_residentes"] / g["llegadas"]).round(3)
    g["pct_oferta_imputada"] = (100 * g["disp_imputada"] / g["cuartos_disponibles"]).round(3)
    return g.drop(columns="disp_imputada")


def integrar(destino_mes: pd.DataFrame, tc_mes: pd.DataFrame, infl: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = destino_mes.merge(tc_mes, on="periodo", how="left").merge(infl, on="periodo", how="left")
    out["id_indicadores"] = "banxico|" + out["periodo"]
    reporte = {
        "registros_datatur_destino_mes": int(len(destino_mes)),
        "registros_integrados": int(len(out)),
        "periodos_sin_tipo_cambio": sorted(out.loc[out["tipo_cambio"].isna(), "periodo"].unique().tolist()),
        "periodos_sin_inflacion": sorted(out.loc[out["inflacion_anual_pct"].isna(), "periodo"].unique().tolist()),
        "cobertura_banxico_fuera_de_datatur": sorted(set(tc_mes["periodo"]) - set(destino_mes["periodo"]))[:3]
        + ["..."],
    }
    return out, reporte
