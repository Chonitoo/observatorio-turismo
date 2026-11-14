"""Pruebas del pipeline Bronce → Plata → Oro (E1)."""
import numpy as np
import pandas as pd
import pytest

from src.pipeline import atipicos, calidad, faltantes, integracion, transformacion


def _registro(**cambios):
    base = dict(archivo_origen="x", fila_origen=2, anio=2019, mes=7, tipo_centro="Centros de Playa",
                subtipo_centro="Otros", centro="Manzanillo", categoria="3 estrellas",
                cuartos_disponibles=1000.0, cuartos_ocupados_no_residentes=50.0,
                cuartos_ocupados_residentes=450.0, llegada_turistas_no_residentes=40.0,
                llegada_turistas_residentes=400.0, turistas_noche_no_residentes=100.0,
                turistas_noche_residentes=900.0)
    base.update(cambios)
    return base


# --- Puerta de Calidad ------------------------------------------------------
def test_puerta_manda_a_cuarentena_con_motivo_y_no_pierde_registros():
    df = pd.DataFrame([
        _registro(),
        _registro(mes=8, cuartos_ocupados_residentes=2000.0),                    # R1
        _registro(mes=9, llegada_turistas_residentes=0.0, llegada_turistas_no_residentes=0.0),  # R2
        _registro(mes=13),                                                      # mes inválido
        _registro(mes=10, categoria="7 estrellas"),                             # dominio
    ])
    ok, q, r = calidad.puerta(df, calidad.esquema_datatur("entrada"), "prueba", "test")
    assert len(ok) + len(q) == len(df)            # nunca se borra en silencio
    assert len(ok) == 1 and len(q) == 4
    assert q["motivo"].str.len().gt(0).all()
    motivos = " ".join(q["motivo"])
    assert "R1" in motivos and "R2" in motivos and "mes fuera de 1-12" in motivos
    assert "categoría desconocida" in motivos


def test_puerta_detecta_duplicados():
    df = pd.DataFrame([_registro(), _registro()])
    ok, q, _ = calidad.puerta(df, calidad.esquema_datatur("entrada"), "prueba", "test")
    assert len(ok) == 0 and q["motivo"].str.contains("R5").all()


def test_puerta_plata_no_admite_nulos():
    df = pd.DataFrame([_registro(turistas_noche_residentes=np.nan)]).assign(imputado=False)
    _, q_entrada, _ = calidad.puerta(df.drop(columns="imputado"), calidad.esquema_datatur("entrada"), "p", "t")
    _, q_plata, _ = calidad.puerta(df, calidad.esquema_datatur("plata"), "p", "t")
    assert len(q_entrada) == 0 and len(q_plata) == 1


# --- Faltantes -------------------------------------------------------------
def _serie(meses_presentes):
    filas = []
    for i in meses_presentes:
        anio, mes = 2016 + (i - 1) // 12, (i - 1) % 12 + 1
        filas.append(_registro(anio=anio, mes=mes, cuartos_disponibles=1000.0 + i))
    return pd.DataFrame(filas)


def test_hueco_interno_corto_se_imputa_y_estructural_no(monkeypatch):
    from src.pipeline import config as C
    monkeypatch.setattr(C, "PERIODO_FIN", "2016-12")
    presentes = [1, 2, 3, 6, 7, 8]           # hueco interno de 2 meses (4-5) y final de 4 (9-12)
    salida, imputados = faltantes.imputar_huecos(_serie(presentes).assign(imputado=False))
    assert sorted(imputados["mes"]) == [4, 5]
    assert salida["imputado"].sum() == 2
    assert imputados["cuartos_disponibles"].between(1003, 1006).all()   # interpolación lineal


def test_imputacion_explicita_por_razon():
    df = _serie(range(1, 13))
    df.loc[5, "turistas_noche_residentes"] = np.nan
    salida, reg = faltantes.imputar_explicitos(df)
    assert salida["turistas_noche_residentes"].notna().all()
    assert salida.loc[5, "imputado"] and reg[0]["razon"] == pytest.approx(900 / 400)


# --- Atípicos --------------------------------------------------------------
def test_z_robusto_e_iqr():
    x = pd.Series([10, 11, 9, 10, 12, 10, 11, 100.0])
    assert atipicos.z_robusto(x).abs().idxmax() == 7
    lo, hi = atipicos.cercas_iqr(x)
    assert x[7] > hi and x[:7].between(lo, hi).all()


# --- Transformación e integración -----------------------------------------
def test_normalizacion():
    df = pd.DataFrame({"a": [0.0, 5.0, 10.0]})
    out, p = transformacion.normalizar(df, ["a"])
    assert out["a_minmax"].tolist() == [0, 0.5, 1]
    assert out["a_z"].mean() == pytest.approx(0) and out["a_z"].std(ddof=0) == pytest.approx(1)
    assert p["a"]["max"] == 10


def test_jerarquias_y_periodo_covid():
    df = pd.DataFrame({"anio": [2019, 2020, 2023], "mes": [9, 4, 7], "centro": ["Manzanillo"] * 3,
                       "tipo_centro": ["Centros de Playa"] * 3})
    out = transformacion.agregar_jerarquias(df)
    assert out["periodo_covid"].tolist() == ["Prepandemia", "Pandemia", "Pospandemia"]
    assert out["temporada"].tolist() == ["Baja", "Alta", "Alta"]
    assert set(out["region"]) == {"Centro Norte"} and set(out["litoral"]) == {"Pacífico"}


def test_tipo_cambio_diario_a_mensual():
    tc = pd.DataFrame({"fecha": pd.to_datetime(["2020-01-02", "2020-01-31", "2020-02-03"]),
                       "tipo_cambio": [18.0, 20.0, 19.0]})
    m = integracion.tipo_cambio_mensual(tc)
    assert m.set_index("periodo").loc["2020-01", "tipo_cambio"] == 19.0
    assert m.set_index("periodo").loc["2020-01", "tipo_cambio_cierre"] == 20.0
