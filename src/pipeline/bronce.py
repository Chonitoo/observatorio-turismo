"""Lectura de la capa Bronce, estandarización mínima de esquema y sello de linaje.

Aquí NO se limpia: sólo se localiza el archivo crudo vigente de cada fuente (según la
bitácora de captura) y se lleva a un esquema tabular común con tipos explícitos. Cualquier
valor que no pueda convertirse queda como nulo y lo detecta la Puerta de Calidad.

Linaje
------
Cada registro recibe, desde el primer momento, las columnas que lo vuelven rastreable:

    id_bronce      identificador único "<fuente>:<sha256[:10]>:<fila>"
    archivo_origen archivo crudo en data/bronze/
    fila_origen    fila (CSV, 1 = encabezado) o posición (JSON) dentro de ese archivo
    sha256_bronce  huella del archivo crudo (verifica que el origen no cambió)
    fecha_ingesta  fecha UTC en que el archivo entró a Bronce (bitácora de captura)

Estas columnas viajan a Plata y se resumen en Oro (ver `linaje.py`).
"""
from __future__ import annotations

import csv
import json
import zipfile

import pandas as pd

from . import config as C

COLS_LINAJE = ["id_bronce", "archivo_origen", "fila_origen", "sha256_bronce", "fecha_ingesta"]


def captura_vigente(fuente: str) -> dict:
    """Última captura exitosa ('nuevo') de una fuente según la bitácora."""
    with C.BITACORA_BRONCE.open(encoding="utf-8", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r["fuente"] == fuente and r["estado"] == "nuevo"]
    if not filas:
        raise FileNotFoundError(f"No hay capturas exitosas de '{fuente}' en la bitácora")
    return filas[-1]


def archivo_vigente(fuente: str) -> str:
    return captura_vigente(fuente)["archivo"]


def _sellar(df: pd.DataFrame, fuente: str, filas) -> pd.DataFrame:
    cap = captura_vigente(fuente)
    df = df.copy()
    df.insert(0, "fecha_ingesta", cap["fecha_utc"])
    df.insert(0, "sha256_bronce", cap["sha256"])
    df.insert(0, "fila_origen", list(filas))
    df.insert(0, "archivo_origen", cap["archivo"])
    df.insert(0, "id_bronce", [f"{fuente}:{cap['sha256'][:10]}:{i}" for i in filas])
    return df


def leer_datatur() -> pd.DataFrame:
    rel = archivo_vigente("datatur")
    # E3: motor PyArrow (lector CSV en C++, multihilo). Los tipos se infieren; si una columna numérica
    # trae texto basura llega como objeto y se convierte con coerce (el valor inválido queda nulo y
    # la Puerta de Calidad lo detecta), igual que antes.
    df = pd.read_csv(C.RAIZ / rel, sep="\t", encoding="utf-8", engine="pyarrow")
    df.columns = [c.strip().lower() for c in df.columns]
    df = _sellar(df, "datatur", range(2, len(df) + 2))   # fila del archivo crudo (1 = encabezado)
    num = [c for c in df.columns if c.startswith(("cuartos_", "llegada_", "turistas_"))]
    for c in num:
        if not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = pd.to_numeric(df[c].astype(str).str.strip(), errors="coerce")
        df[c] = df[c].astype(float)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    for c in ["tipo_centro", "subtipo_centro", "centro", "categoria"]:
        df[c] = df[c].str.strip()
    return df


def _leer_banxico(fuente: str, nombre_valor: str) -> pd.DataFrame:
    rel = archivo_vigente(fuente)
    with (C.RAIZ / rel).open(encoding="utf-8") as f:
        serie = json.load(f)["bmx"]["series"][0]
    df = pd.DataFrame(serie["datos"])
    # Conflictos de esquema con DataTur: la fecha viene como texto dd/mm/aaaa y el valor
    # como texto (puede traer "N/E" = no existe, o comas de miles).
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df[nombre_valor] = pd.to_numeric(df["dato"].str.replace(",", "", regex=False), errors="coerce")
    df["id_serie"] = serie["idSerie"]
    df = _sellar(df[["id_serie", "fecha", nombre_valor]], fuente, range(len(df)))  # posición en datos[]
    return df


def leer_tipo_cambio() -> pd.DataFrame:
    return _leer_banxico("banxico_tipo_cambio_fix", "tipo_cambio")


def leer_inpc() -> pd.DataFrame:
    return _leer_banxico("banxico_inpc", "inpc")


def leer_denue(prefijo_scian: str = "721") -> pd.DataFrame:
    """DENUE de Colima: sólo establecimientos cuyo código SCIAN empieza con `prefijo_scian`
    (721 = servicios de alojamiento temporal). La fila de origen se cuenta sobre el CSV completo."""
    from .geo import COLS_CONSERVADAS
    rel = archivo_vigente("inegi_denue_colima")
    # Conflicto de codificación: DENUE viene en latin-1 (DataTur y Banxico en UTF-8).
    # E3: (1) se lee directo del ZIP como flujo, sin cargar los 22 MB descomprimidos en memoria;
    #     (2) sólo las columnas que el análisis usa (14 de 42): menos tiempo y memoria, y la
    #     minimización de datos personales ocurre desde la lectura (los campos de contacto ni se cargan).
    #     (3) los nombres se normalizan a minúsculas: la edición 11/2026 del DENUE cambió los
    #     encabezados a MAYÚSCULAS (CODIGO_ACT) y el pipeline se detuvo en GitHub Actions.
    with zipfile.ZipFile(C.RAIZ / rel) as z:
        nombre = next(n for n in z.namelist() if n.startswith("conjunto_de_datos/") and n.endswith(".csv"))
        with z.open(nombre) as flujo:
            df = pd.read_csv(flujo, dtype=str, encoding="latin-1",
                             usecols=lambda c: c.strip().lower() in COLS_CONSERVADAS)
    df.columns = [c.strip().lower() for c in df.columns]
    faltan = [c for c in COLS_CONSERVADAS if c not in df.columns]
    if faltan:
        raise RuntimeError(f"Cambio de esquema en el DENUE ({rel}): faltan las columnas {faltan}. "
                           "Revisar el diccionario de datos de la nueva edición y actualizar geo.COLS_CONSERVADAS.")
    df = _sellar(df, "inegi_denue_colima", range(2, len(df) + 2))
    df = df[df["codigo_act"].str.startswith(prefijo_scian, na=False)].copy()
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
    return df


def edicion_denue() -> str:
    """Edición del DENUE vigente según sus metadatos (p. ej. '11/2026'), para citarla correctamente."""
    import re
    rel = archivo_vigente("inegi_denue_colima")
    with zipfile.ZipFile(C.RAIZ / rel) as z:
        meta = next((n for n in z.namelist() if n.startswith("metadatos/")), None)
        texto = z.read(meta).decode("latin-1") if meta else ""
    m = re.search(r"\(DENUE\)\s*(\d{2})_(\d{4})", texto)
    return f"{m.group(1)}/{m.group(2)}" if m else "edición desconocida"


def leer_municipios():
    import geopandas as gpd
    rel = archivo_vigente("inegi_mg_municipios")
    g = gpd.read_file(C.RAIZ / rel)
    g = _sellar(g, "inegi_mg_municipios", range(len(g)))  # posición en features[]
    for c in ["pob_total", "pob_femenina", "pob_masculina", "total_viviendas_habitadas"]:
        g[c] = pd.to_numeric(g[c], errors="coerce")
    return gpd.GeoDataFrame(g, geometry="geometry", crs=g.crs)
