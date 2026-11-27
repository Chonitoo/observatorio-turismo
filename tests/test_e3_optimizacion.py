"""Pruebas E3: correcciones de errores introducidas en la optimización."""
import numpy as np
import pandas as pd

from src.pipeline import calidad, faltantes
from src.pipeline import config as C
from tests.test_pipeline import _registro


def test_r6_detecta_estadia_implausible_desde_la_entrada():
    df = pd.DataFrame([_registro(), _registro(mes=8, llegada_turistas_residentes=10.0,
                                              llegada_turistas_no_residentes=0.0,
                                              turistas_noche_residentes=900.0, turistas_noche_no_residentes=0.0,
                                              cuartos_ocupados_residentes=500.0)])
    ok, q, _ = calidad.puerta(df, calidad.esquema_datatur("entrada"), "prueba", "test")
    assert len(ok) == 1 and q["motivo"].str.contains("R6").all()


def _rejilla_simple(meses_presentes, inicio="2020-01"):
    per = pd.period_range(inicio, periods=12, freq="M")
    return pd.DataFrame({"centro": "X", "categoria": "3 estrellas", "periodo": per,
                         "falta": [i not in meses_presentes for i in range(12)]})


def test_huecos_en_pandemia_no_se_imputan():
    # hueco de 2 meses en abr-may 2020 (meses de choque) y otro en oct-nov 2019 (normal)
    g = faltantes.clasificar_huecos(_rejilla_simple({0, 1, 2, 5, 6, 7, 8, 9, 10, 11}))
    assert set(g.loc[g.falta, "tipo_hueco"]) == {"en_choque"}
    g2 = faltantes.clasificar_huecos(_rejilla_simple({0, 1, 2, 5, 6, 7, 8, 9, 10, 11}, inicio="2018-01"))
    assert set(g2.loc[g2.falta, "tipo_hueco"]) == {"interno_corto"}


def test_clasificacion_vectorizada_equivale_a_reglas():
    g = faltantes.clasificar_huecos(_rejilla_simple({2, 3, 7, 8}, inicio="2017-01"))
    t = g.set_index(g.periodo.astype(str))["tipo_hueco"]
    assert t["2017-01"] == "estructural"          # al inicio
    assert t["2017-05"] == "interno_corto"        # hueco interno de 3 meses (may-jul)
    assert t["2017-12"] == "estructural"          # al final
    assert g.loc[g.periodo.astype(str) == "2017-05", "largo_hueco"].iloc[0] == 3


def test_imputacion_nunca_emite_registros_inconsistentes(monkeypatch):
    monkeypatch.setattr(C, "PERIODO_FIN", "2016-12")
    filas = []
    for i in [1, 2, 3, 6, 7, 8]:
        r = _registro(anio=2016, mes=i, id_bronce=f"datatur:abc:{i}", fila_origen=i)
        if i == 3:   # vecino previo con ocupados=0: antes generaba tasa de llegadas = 0 en el hueco
            r.update(cuartos_ocupados_residentes=0.0, cuartos_ocupados_no_residentes=0.0,
                     llegada_turistas_residentes=0.0, llegada_turistas_no_residentes=0.0,
                     turistas_noche_residentes=0.0, turistas_noche_no_residentes=0.0)
        filas.append(r)
    salida, imp = faltantes.imputar_huecos(pd.DataFrame(filas).assign(imputado=False))
    _, q, _ = calidad.puerta(imp.drop(columns=["base_imputacion"]).assign(imputado=True),
                             calidad.esquema_datatur("plata"), "prueba", "test")
    assert len(q) == 0
