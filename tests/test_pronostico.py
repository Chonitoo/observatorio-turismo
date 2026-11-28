"""Pruebas del pronóstico (pregunta analítica E1): forma, coherencia de bandas y validación."""
import json

import pandas as pd
import pytest

from src import pronostico

pytestmark = pytest.mark.skipif(not pronostico.SALIDA.exists(), reason="ejecutar: python -m src.pronostico")


@pytest.fixture(scope="module")
def p():
    return pd.read_csv(pronostico.SALIDA)


def test_doce_meses_por_destino(p):
    assert p.groupby("centro").size().eq(pronostico.HORIZONTE).all()


def test_bandas_coherentes(p):
    assert (p.li95 <= p.li80 + 1e-9).all() and (p.li80 <= p.pronostico_pct + 1e-9).all()
    assert (p.pronostico_pct <= p.ls80 + 1e-9).all() and (p.ls80 <= p.ls95 + 1e-9).all()
    assert p[["pronostico_pct", "li95", "ls95"]].stack().between(0, 100).all()


def test_pronostico_empieza_despues_del_ultimo_dato(p):
    assert (p.periodo > p.ultimo_dato).all()


def test_metodo_elegido_por_validacion():
    m = json.loads(pronostico.METRICAS.read_text(encoding="utf-8"))
    for centro, r in m["por_destino"].items():
        mod, ing = r["modelo"]["mae"], r["ingenuo"]["mae"]
        esperado = "SARIMAX" if float(mod) < float(ing) else "Ingenuo"
        assert r["metodo_publicado"].startswith(esperado), centro
    assert m["mae_mediano_publicado_pts"] <= m["mae_mediano_ingenuo_pts"]
