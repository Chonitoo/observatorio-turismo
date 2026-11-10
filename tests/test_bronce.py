"""Pruebas de la capa Bronce: integridad de la serie histórica y de la máquina de captura."""
import csv
import hashlib
from pathlib import Path

import pandas as pd

from src import comun

RAIZ = Path(__file__).resolve().parents[1]
SEMILLA = RAIZ / "data" / "bronze" / "datatur" / "Base70centros_2026-11-10_manual.csv"
SHA_SEMILLA = "a8ca3f9bf34edf46321a45c1abcd3f774363d02db0395f1d6132b8a7c4d7d671"


def test_semilla_no_fue_modificada():
    """Bronce es inmutable: el crudo debe conservar su huella original."""
    assert hashlib.sha256(SEMILLA.read_bytes()).hexdigest() == SHA_SEMILLA


def test_serie_tiene_al_menos_36_periodos_para_colima():
    df = pd.read_csv(SEMILLA, sep="\t", dtype={"mes": str})
    for centro in ("Manzanillo", "Colima"):
        periodos = df.loc[df.centro == centro, ["anio", "mes"]].drop_duplicates()
        assert len(periodos) >= 36, f"{centro}: sólo {len(periodos)} periodos"


def test_columnas_esperadas():
    df = pd.read_csv(SEMILLA, sep="\t", nrows=5)
    esperadas = {"anio", "mes", "centro", "categoria", "cuartos_disponibles",
                 "cuartos_ocupados_residentes", "cuartos_ocupados_no_residentes"}
    assert esperadas <= set(df.columns)


def test_bitacora_registra_y_detecta_duplicados(tmp_path, monkeypatch):
    monkeypatch.setattr(comun, "BRONCE", tmp_path)
    monkeypatch.setattr(comun, "BITACORA", tmp_path / "_bitacora.csv")
    comun.registrar(comun.ResultadoCaptura("prueba", "https://x", "ok", 200, "nuevo", 3, "abc", "f"))
    assert comun.ultimo_sha("prueba") == "abc"
    assert comun.ultimo_sha("otra") == ""
    with (tmp_path / "_bitacora.csv").open(encoding="utf-8") as f:
        assert list(csv.DictReader(f))[0]["estado"] == "nuevo"


def test_user_agent_se_identifica():
    assert "github.com" in comun.USER_AGENT and "academico" in comun.USER_AGENT
