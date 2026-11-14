"""Lectura de la capa Bronce y estandarización mínima de esquema.

Aquí NO se limpia: sólo se localiza el archivo crudo más reciente de cada fuente
(según la bitácora de captura) y se lleva a un esquema tabular común con nombres
en snake_case y tipos explícitos. Cualquier valor que no pueda convertirse queda
como nulo y será detectado por la Puerta de Calidad.
"""
from __future__ import annotations

import csv
import json

import pandas as pd

from . import config as C


def archivo_vigente(fuente: str) -> str:
    """Ruta (relativa a la raíz) del último archivo crudo exitoso de una fuente."""
    with C.BITACORA_BRONCE.open(encoding="utf-8", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r["fuente"] == fuente and r["estado"] == "nuevo"]
    if not filas:
        raise FileNotFoundError(f"No hay capturas exitosas de '{fuente}' en la bitácora")
    return filas[-1]["archivo"]


def leer_datatur() -> pd.DataFrame:
    rel = archivo_vigente("datatur")
    df = pd.read_csv(C.RAIZ / rel, sep="\t", dtype=str, encoding="utf-8")
    df.columns = [c.strip().lower() for c in df.columns]
    df.insert(0, "fila_origen", range(2, len(df) + 2))  # fila del archivo crudo (1 = encabezado)
    df.insert(0, "archivo_origen", rel)
    num = [c for c in df.columns if c.startswith(("cuartos_", "llegada_", "turistas_"))]
    for c in num:
        df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce")
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
    df["archivo_origen"] = rel
    df["fila_origen"] = range(len(df))
    return df[["archivo_origen", "fila_origen", "id_serie", "fecha", nombre_valor]]


def leer_tipo_cambio() -> pd.DataFrame:
    return _leer_banxico("banxico_tipo_cambio_fix", "tipo_cambio")


def leer_inpc() -> pd.DataFrame:
    return _leer_banxico("banxico_inpc", "inpc")
