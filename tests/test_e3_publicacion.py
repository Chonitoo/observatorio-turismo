"""Pruebas E3: dataset publicado (licencia, metadatos, integridad y privacidad)."""
import hashlib
import json

import pandas as pd
import pytest

from src import publicar
from src.pipeline import geo

D = publicar.DESTINO
pytestmark = pytest.mark.skipif(not (D / "datapackage.json").exists(), reason="ejecutar: python -m src.publicar")


def test_archivos_obligatorios():
    for f in ["README.md", "LICENSE.md", "datapackage.json", "diccionario_datos.csv", "SHA256SUMS.txt"]:
        assert (D / f).exists(), f


def test_licencia_abierta_declarada():
    pkg = json.loads((D / "datapackage.json").read_text(encoding="utf-8"))
    assert pkg["licenses"][0]["name"] == "CC-BY-4.0"
    assert "Atribución 4.0" in (D / "LICENSE.md").read_text(encoding="utf-8")


def test_sumas_sha256_coinciden():
    for linea in (D / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        sha, nombre = linea.split("  ", 1)
        assert hashlib.sha256((D / nombre).read_bytes()).hexdigest() == sha, nombre


def test_diccionario_cubre_todas_las_columnas():
    dic = pd.read_csv(D / "diccionario_datos.csv")
    for tabla in publicar.DICCIONARIO:
        cols = set(pd.read_csv(D / f"{tabla}.csv", nrows=1).columns)
        assert cols == set(dic.loc[dic.tabla == tabla, "columna"]), tabla
        assert dic.loc[dic.tabla == tabla, "descripcion"].str.len().gt(10).all()


def test_sin_datos_personales():
    for tabla in publicar.DICCIONARIO:
        cols = set(pd.read_csv(D / f"{tabla}.csv", nrows=1).columns)
        assert not cols & set(geo.COLS_DESCARTADAS_PRIVACIDAD), tabla


def test_parquet_equivale_a_csv():
    for tabla in publicar.DICCIONARIO:
        assert len(pd.read_parquet(D / "parquet" / f"{tabla}.parquet")) == len(pd.read_csv(D / f"{tabla}.csv"))
