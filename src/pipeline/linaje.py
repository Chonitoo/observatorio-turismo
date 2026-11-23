"""Linaje y trazabilidad: de cada registro de Oro a su origen en Bronce.

Cada tabla de Oro tiene un identificador `id_oro`. La tabla `data/gold/linaje_oro.csv`
(formato largo) enumera, para cada `id_oro`, todos los registros crudos que lo produjeron:

    id_oro | tabla_oro | fuente | id_bronce | archivo_origen | fila_origen | sha256_bronce | fecha_ingesta | rol

`rol` describe la transformación: agregación, promedio mensual, variación anual, imputación,
unión espacial, etc. `rastrear(id_oro)` vuelve a abrir los archivos crudos y devuelve las filas
originales; `verificar()` comprueba que todo el linaje resuelve a archivos existentes cuya huella
SHA-256 coincide con la bitácora de captura.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from functools import lru_cache

import pandas as pd

from . import config as C

ARCHIVO_LINAJE = C.ORO / "linaje_oro.csv"
COLS = ["id_oro", "tabla_oro", "fuente", "id_bronce", "archivo_origen", "fila_origen",
        "sha256_bronce", "fecha_ingesta", "rol"]


def _catalogo_capturas() -> pd.DataFrame:
    b = pd.read_csv(C.BITACORA_BRONCE, dtype=str)
    return b[b["estado"] == "nuevo"].set_index("archivo")


def _filas(df: pd.DataFrame, tabla: str, fuente: str, rol: str, col_id="id_oro") -> pd.DataFrame:
    out = df[[col_id, "id_bronce", "archivo_origen", "fila_origen", "sha256_bronce", "fecha_ingesta"]].copy()
    out = out.rename(columns={col_id: "id_oro"})
    out.insert(1, "tabla_oro", tabla)
    out.insert(2, "fuente", fuente)
    out["rol"] = rol
    return out[COLS]


def construir(plata_datatur: pd.DataFrame, oro_destino: pd.DataFrame, tc: pd.DataFrame,
              inpc: pd.DataFrame, extra: list[pd.DataFrame] | None = None) -> pd.DataFrame:
    """Tabla larga de linaje para las tablas de Oro derivadas de DataTur + Banxico."""
    partes = []
    pd_ = plata_datatur.copy()
    pd_["periodo"] = pd_["anio"].astype(int).astype(str) + "-" + pd_["mes"].astype(int).astype(str).str.zfill(2)
    pd_["id_oro"] = pd_["centro"] + "|" + pd_["periodo"]
    pd_ = pd_[pd_["id_oro"].isin(set(oro_destino["id_oro"]))]

    reales = pd_[~pd_["id_bronce"].str.startswith("IMPUTADO")]
    partes.append(_filas(reales, "destino_mes", "datatur", "agregación centro×categoría→centro"))
    imp = pd_[pd_["id_bronce"].str.startswith("IMPUTADO")].copy()
    if len(imp):
        # un registro imputado se rastrea a los dos registros reales de los que se interpoló
        base = imp.assign(id_base=imp["base_imputacion"].str.split("|")).explode("id_base")
        cat = reales.set_index("id_bronce")
        base = base[base["id_base"].isin(cat.index)]
        b = cat.loc[base["id_base"], ["archivo_origen", "fila_origen", "sha256_bronce", "fecha_ingesta"]]
        b = b.reset_index().rename(columns={"index": "id_bronce"})
        b["id_oro"] = base["id_oro"].to_numpy()
        partes.append(_filas(b, "destino_mes", "datatur", "base de imputación (hueco interno)"))

    # Banxico es nacional: el mismo indicador mensual se replica a todos los destinos. Para no
    # repetir ~150 mil filas, se rastrea una vez por mes con id_oro = "banxico|AAAA-MM";
    # cada fila de destino_mes apunta a él (columna id_indicadores).
    per = pd.DataFrame({"periodo": sorted(oro_destino["periodo"].unique())})
    per["id_oro"] = "banxico|" + per["periodo"]
    t = tc.assign(periodo=tc["fecha"].dt.to_period("M").astype(str)).merge(per, on="periodo")
    partes.append(_filas(t, "indicadores_mes", "banxico_tipo_cambio", "promedio mensual del FIX diario"))
    i = inpc.assign(periodo=inpc["fecha"].dt.to_period("M").astype(str))
    i12 = i.assign(periodo=(inpc["fecha"] + pd.DateOffset(years=1)).dt.to_period("M").astype(str))
    for sub, rol in [(i, "INPC del mes"), (i12, "INPC 12 meses antes (variación anual)")]:
        partes.append(_filas(sub.merge(per, on="periodo"), "indicadores_mes", "banxico_inpc", rol))
    partes += extra or []
    lin = pd.concat(partes, ignore_index=True)
    return lin


@lru_cache(maxsize=16)
def _crudo(archivo: str):
    ruta = C.RAIZ / archivo
    if archivo.endswith(".zip"):
        with zipfile.ZipFile(ruta) as z:
            n = next(x for x in z.namelist() if x.startswith("conjunto_de_datos/") and x.endswith(".csv"))
            return pd.read_csv(io.BytesIO(z.read(n)), dtype=str, encoding="latin-1")
    if archivo.endswith(".csv"):
        return pd.read_csv(ruta, sep="\t", dtype=str, encoding="utf-8")
    with ruta.open(encoding="utf-8") as f:
        d = json.load(f)
    if "bmx" in d:
        return pd.DataFrame(d["bmx"]["series"][0]["datos"])
    return pd.DataFrame([ft["properties"] for ft in d["features"]])


def fila_cruda(archivo: str, fila: int) -> dict:
    """Devuelve la fila original del archivo crudo (CSV: fila 2 = primer dato; JSON: posición)."""
    df = _crudo(archivo)
    pos = int(fila) - 2 if archivo.endswith((".csv", ".zip")) else int(fila)
    return df.iloc[pos].to_dict()


def rastrear(id_oro: str, linaje: pd.DataFrame | None = None, limite: int = 50) -> pd.DataFrame:
    lin = pd.read_csv(ARCHIVO_LINAJE, dtype=str) if linaje is None else linaje
    ids = {id_oro}
    if id_oro.count("|") == 1 and not id_oro.startswith(("banxico|", "municipio|")):
        ids.add("banxico|" + id_oro.split("|")[1])     # destino_mes → indicadores del mes
    sel = (lin[lin["id_oro"].isin(ids)].groupby(["fuente", "rol"], group_keys=False)
           .head(limite).copy())
    sel["registro_crudo"] = [fila_cruda(a, f) for a, f in zip(sel["archivo_origen"], sel["fila_origen"])]
    return sel


def verificar(linaje: pd.DataFrame | None = None) -> dict:
    """Integridad del linaje: archivos existentes, huella SHA-256 vigente y fila dentro de rango."""
    lin = pd.read_csv(ARCHIVO_LINAJE, dtype=str) if linaje is None else linaje
    cat = _catalogo_capturas()
    archivos = lin["archivo_origen"].unique()
    problemas = []
    for a in archivos:
        ruta = C.RAIZ / a
        if not ruta.exists():
            problemas.append(f"no existe {a}")
            continue
        sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
        if a not in cat.index or cat.loc[a, "sha256"] != sha:
            problemas.append(f"huella distinta o no registrada: {a}")
        n = len(_crudo(a))
        filas = pd.to_numeric(lin.loc[lin["archivo_origen"] == a, "fila_origen"])
        maximo = n + 1 if a.endswith((".csv", ".zip")) else n - 1
        if filas.max() > maximo:
            problemas.append(f"fila fuera de rango en {a}")
    return {"registros_linaje": int(len(lin)), "ids_oro": int(lin["id_oro"].nunique()),
            "archivos_bronce": len(archivos), "problemas": problemas, "integro": not problemas}
