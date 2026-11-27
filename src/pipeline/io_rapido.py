"""Escritura rápida y robusta de tablas (E3).

`escribir_csv` usa el escritor CSV de PyArrow (C++), varias veces más rápido que `DataFrame.to_csv`.
Las fechas se escriben como AAAA-MM-DD, los nulos como celda vacía y los booleanos como true/false.
Si una tabla tiene valores con comas (o tipos mezclados que Arrow no representa) se usa pandas.

Robustez: se escribe primero a un archivo temporal en la misma carpeta y luego se reemplaza el
destino de forma atómica (`os.replace`). Si otro proceso tiene el archivo abierto o mapeado
(antivirus, indexador, una hoja de cálculo; WinError 32/1224 en Windows), se reintenta con espera
creciente en lugar de abortar todo el pipeline o dejar un archivo a medio escribir.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

REINTENTOS = 6


def _reemplazar(tmp: Path, destino: Path) -> None:
    for intento in range(REINTENTOS):
        try:
            os.replace(tmp, destino)
            return
        except PermissionError:
            if intento == REINTENTOS - 1:
                raise
            time.sleep(0.25 * 2 ** intento)   # 0.25, 0.5, 1, 2, 4 s


def escribir_csv(df: pd.DataFrame, ruta: Path) -> None:
    ruta = Path(ruta)
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m-%d")
        elif isinstance(d[c].dtype, pd.CategoricalDtype):
            d[c] = d[c].astype(str).where(d[c].notna())
    tmp = ruta.with_name(f".{ruta.name}.{os.getpid()}.tmp")
    try:
        try:
            tabla = pa.Table.from_pandas(d, preserve_index=False)
            try:
                # sin comillas (como pandas): archivos más chicos. Arrow se niega si algún valor
                # contiene coma, comillas o salto de línea; en ese caso se usa pandas, que entrecomilla
                # sólo esos valores (mismo formato que antes de la optimización).
                pacsv.write_csv(tabla, str(tmp), pacsv.WriteOptions(quoting_style="none"))
            except pa.ArrowInvalid:
                d.to_csv(tmp, index=False)   # comillas sólo en los valores que las necesitan
        except (pa.ArrowInvalid, pa.ArrowTypeError, pa.ArrowNotImplementedError):
            d.to_csv(tmp, index=False)
        _reemplazar(tmp, ruta)
    finally:
        if tmp.exists():
            tmp.unlink()
