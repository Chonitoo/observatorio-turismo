"""Escritura rápida de tablas (E3).

`escribir_csv` usa el escritor CSV de PyArrow (C++), varias veces más rápido que `DataFrame.to_csv`.
Las fechas se escriben como AAAA-MM-DD y los nulos como celda vacía. Si una columna tiene tipos
mezclados que Arrow no puede representar, se recurre a pandas para no fallar.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv


def escribir_csv(df: pd.DataFrame, ruta: Path) -> None:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m-%d")
        elif isinstance(d[c].dtype, pd.CategoricalDtype):
            d[c] = d[c].astype(str).where(d[c].notna())
    try:
        tabla = pa.Table.from_pandas(d, preserve_index=False)
        pacsv.write_csv(tabla, str(ruta), pacsv.WriteOptions(quoting_style="needed"))
    except (pa.ArrowInvalid, pa.ArrowTypeError, pa.ArrowNotImplementedError):
        d.to_csv(ruta, index=False)
