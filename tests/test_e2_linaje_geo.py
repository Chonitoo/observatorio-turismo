"""Pruebas E2: linaje Oro → Bronce y rama geoespacial (sobre las salidas reales del pipeline)."""
import hashlib

import pandas as pd
import pytest

from src.pipeline import config as C
from src.pipeline import geo, linaje

pytestmark = pytest.mark.skipif(not linaje.ARCHIVO_LINAJE.exists(),
                                reason="ejecutar antes: python -m src.pipeline.ejecutar")


@pytest.fixture(scope="module")
def lin():
    return pd.read_csv(linaje.ARCHIVO_LINAJE, dtype=str)


def test_todo_registro_oro_tiene_linaje(lin):
    ids = set(lin["id_oro"])
    for tabla in ["destino_mes", "establecimientos_hospedaje", "municipio_hospedaje"]:
        oro = pd.read_csv(C.ORO / f"{tabla}.csv", usecols=["id_oro"])
        assert set(oro["id_oro"]) <= ids, tabla


def test_linaje_tiene_fecha_de_ingesta_y_huella(lin):
    assert lin["fecha_ingesta"].str.match(r"^\d{4}-\d{2}-\d{2}T").all()
    assert lin["sha256_bronce"].str.len().eq(64).all()


def test_huellas_coinciden_con_archivos_bronce(lin):
    for archivo, sha in lin[["archivo_origen", "sha256_bronce"]].drop_duplicates().itertuples(index=False):
        assert hashlib.sha256((C.RAIZ / archivo).read_bytes()).hexdigest() == sha


def test_rastreo_devuelve_la_fila_cruda_correcta():
    r = linaje.rastrear("Manzanillo|2024-07")
    dt = r[r["fuente"] == "datatur"]
    assert len(dt) >= 1
    for crudo in dt["registro_crudo"]:
        assert crudo["centro"] == "Manzanillo" and crudo["anio"] == "2024" and crudo["mes"] == "07"
    assert (r["fuente"] == "banxico_tipo_cambio").any()


def test_rastreo_establecimiento_denue():
    est = pd.read_csv(C.ORO / "establecimientos_hospedaje.csv", dtype=str)
    fila = est.iloc[0]
    r = linaje.rastrear(fila["id_oro"])
    assert r["registro_crudo"].iloc[0]["id"] == fila["id"]


def test_privacidad_sin_columnas_personales():
    for tabla in [C.PLATA / "denue_hospedaje_colima.csv", C.ORO / "establecimientos_hospedaje.csv"]:
        cols = set(pd.read_csv(tabla, nrows=1).columns)
        assert not cols & set(geo.COLS_DESCARTADAS_PRIVACIDAD), tabla


def test_municipios_suman_oferta_estatal():
    m = pd.read_csv(C.ORO / "municipio_hospedaje.csv")
    est = pd.read_csv(C.ORO / "establecimientos_hospedaje.csv")
    assert len(m) == 10 and m["establecimientos"].sum() == len(est)
    assert m["pct_oferta_estatal"].sum() == pytest.approx(100, abs=0.5)
