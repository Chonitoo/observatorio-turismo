"""Puerta de Calidad automática (Pandera) con cuarentena.

Cada esquema define reglas de tipo, dominio, rango y consistencia lógica. La función
`puerta()` valida en modo *lazy* (reúne TODAS las fallas, no sólo la primera), separa
los registros que fallan y los manda a cuarentena con el motivo documentado:
ningún registro se elimina en silencio.

    Bronce ──► [Puerta 1: entrada] ──► limpieza / imputación ──► [Puerta 2: Plata] ──► Plata
    Plata  ──► integración / transformación ──► [Puerta 3: Oro] ──► Oro
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors

from . import config as C

LLAVE_DATATUR = ["anio", "mes", "centro", "categoria"]
CONTEOS = [
    "cuartos_disponibles", "cuartos_ocupados_no_residentes", "cuartos_ocupados_residentes",
    "llegada_turistas_no_residentes", "llegada_turistas_residentes",
    "turistas_noche_no_residentes", "turistas_noche_residentes",
]


# --- Reglas de consistencia lógica (a nivel registro) ----------------------
# Los nulos se toleran en R3/R4 porque en la etapa de entrada se imputan después;
# en la etapa Plata las columnas ya no admiten nulos.
def _ocupados(d):
    return d.cuartos_ocupados_residentes + d.cuartos_ocupados_no_residentes


def _llegadas(d):
    return d.llegada_turistas_residentes + d.llegada_turistas_no_residentes


def _noches(d):
    return d.turistas_noche_residentes + d.turistas_noche_no_residentes


REGLAS_DATATUR = [
    pa.Check(lambda d: _ocupados(d) <= d.cuartos_disponibles, name="R1_ocupados_le_disponibles",
             error="R1: cuartos ocupados mayores que cuartos disponibles"),
    pa.Check(lambda d: (_ocupados(d) == 0) | (_llegadas(d) > 0), name="R2_ocupacion_sin_llegadas",
             error="R2: hay cuartos ocupados pero cero llegadas de turistas"),
    pa.Check(lambda d: (_noches(d) >= _llegadas(d)) | _noches(d).isna(), name="R3_noches_ge_llegadas",
             error="R3: turistas-noche menores que llegadas (cada llegada pernocta al menos 1 noche)"),
    pa.Check(lambda d: (_ocupados(d) == 0) | _noches(d).isna()
             | (_noches(d) <= C.DENSIDAD_MAX * _ocupados(d)),
             name="R4_densidad_plausible",
             error=f"R4: más de {C.DENSIDAD_MAX:g} turistas por cuarto ocupado"),
    pa.Check(lambda d: ~d.duplicated(LLAVE_DATATUR, keep=False), name="R5_llave_unica",
             error="R5: registro duplicado (anio, mes, centro, categoria)"),
]


def _conteo(nullable: bool = False) -> pa.Column:
    return pa.Column(float, [pa.Check.ge(0, error="valor negativo")], nullable=nullable)


def esquema_datatur(etapa: str) -> pa.DataFrameSchema:
    """etapa='entrada' tolera nulos en conteos (se imputan después); etapa='plata' no."""
    tolera = etapa == "entrada"
    anio_max = datetime.now().year
    columnas = {
        "anio": pa.Column(int, pa.Check.in_range(2016, anio_max, error=f"año fuera de 2016-{anio_max}")),
        "mes": pa.Column(int, pa.Check.in_range(1, 12, error="mes fuera de 1-12")),
        "tipo_centro": pa.Column(str, pa.Check.isin(C.TIPOS_CENTRO, error="tipo_centro desconocido")),
        "subtipo_centro": pa.Column(str, nullable=False),
        "centro": pa.Column(str, pa.Check.isin(list(C.CENTRO_ESTADO), error="centro fuera del catálogo")),
        "categoria": pa.Column(str, pa.Check.isin(C.CATEGORIAS, error="categoría desconocida")),
        "cuartos_disponibles": pa.Column(float, pa.Check.gt(0, error="cuartos disponibles <= 0")),
        **{c: _conteo(nullable=tolera) for c in CONTEOS if c != "cuartos_disponibles"},
    }
    if etapa == "plata":
        columnas["imputado"] = pa.Column(bool)
    return pa.DataFrameSchema(columnas, checks=REGLAS_DATATUR, coerce=True, strict=False,
                              name=f"datatur_{etapa}")


def esquema_banxico(valor: str, rango: tuple[float, float], diario: bool) -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "fecha": pa.Column("datetime64[ns]", [
                pa.Check(lambda s: s >= pd.Timestamp("2015-01-01"), error="fecha anterior a 2015"),
                pa.Check(lambda s: s <= pd.Timestamp.now(), error="fecha futura"),
            ], nullable=False),
            valor: pa.Column(float, pa.Check.in_range(*rango, error=f"{valor} fuera de rango {rango}"),
                             nullable=False),
        },
        checks=[pa.Check(lambda d: ~d.fecha.duplicated(keep=False), error="fecha duplicada")]
        + ([] if diario else [pa.Check(lambda d: d.fecha.dt.day == 1, error="fecha mensual no es día 1")]),
        coerce=True, name=f"banxico_{valor}",
    )


def esquema_oro() -> pa.DataFrameSchema:
    pct = pa.Check.in_range(0, 100, error="porcentaje fuera de 0-100")
    return pa.DataFrameSchema(
        {
            "periodo": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}$", error="periodo no es AAAA-MM")),
            "centro": pa.Column(str),
            "ocupacion_pct": pa.Column(float, pct),
            # Las razones son nulas (0/0) sólo cuando el destino tuvo cero llegadas (cierre por COVID);
            # la regla O1 exige que ese sea el único caso de nulo.
            "pct_no_residentes": pa.Column(float, pct, nullable=True),
            "estadia_promedio": pa.Column(float, pa.Check.in_range(1, 30, error="estadía fuera de 1-30 noches"),
                                          nullable=True),
            "densidad": pa.Column(float, pa.Check.in_range(0.5, C.DENSIDAD_MAX, error="densidad implausible"),
                                  nullable=True),
            "tipo_cambio": pa.Column(float, pa.Check.in_range(*C.TIPO_CAMBIO_RANGO)),
            "inflacion_anual_pct": pa.Column(float, pa.Check.in_range(-10, 50), nullable=True),
            "ocupacion_pct_minmax": pa.Column(float, pa.Check.in_range(0, 1)),
        },
        checks=[pa.Check(lambda d: ~d.duplicated(["periodo", "centro"], keep=False),
                         error="duplicado (periodo, centro)"),
                pa.Check(lambda d: d.estadia_promedio.notna() | (d.llegadas == 0),
                         error="O1: razón nula sin que las llegadas sean cero")],
        coerce=True, name="oro_destino_mes",
    )


# --- La puerta -------------------------------------------------------------
def puerta(df: pd.DataFrame, esquema: pa.DataFrameSchema, fuente: str, etapa: str
           ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Valida `df`. Devuelve (validos, cuarentena, resumen).

    La cuarentena conserva el registro original completo más:
    motivo (texto legible), reglas (identificadores), etapa, fuente y fecha_proceso.
    """
    df = df.reset_index(drop=True)
    try:
        validos = esquema.validate(df, lazy=True)
        cuarentena = df.iloc[0:0].copy()
        fallas = pd.DataFrame(columns=["index", "column", "check"])
    except SchemaErrors as err:
        fallas = err.failure_cases.copy()
        sin_fila = fallas["index"].isna()
        if sin_fila.any():
            # Fallas de toda una columna (p. ej. columna ausente): no se puede filtrar por
            # registro, así que la fuente completa queda detenida.
            raise RuntimeError(
                f"Puerta {etapa}/{fuente}: fallas estructurales de esquema\n"
                f"{fallas[sin_fila].to_string()}"
            ) from err
        fallas["index"] = fallas["index"].astype(int)
        malos = sorted(fallas["index"].unique())
        cuarentena = df.loc[malos].copy()
        # Reglas de columna: "columna: regla". Reglas de registro (DataFrameSchema): sólo la regla,
        # porque Pandera las reporta una vez por cada columna del registro.
        es_columna = fallas["schema_context"] == "Column"
        txt = np.where(es_columna, fallas["column"].astype(str) + ": " + fallas["check"].astype(str),
                       fallas["check"].astype(str))
        motivos = (fallas.assign(txt=txt)
                   .groupby("index")["txt"].agg(lambda s: " | ".join(sorted(set(s)))))
        cuarentena["motivo"] = motivos.reindex(malos).values
        validos = esquema.validate(df.drop(index=malos), lazy=True)  # revalidación estricta

    sello = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cuarentena = cuarentena.assign(etapa=etapa, fuente=fuente, fecha_proceso=sello)
    resumen = {
        "fuente": fuente, "etapa": etapa, "esquema": esquema.name,
        "registros_entrada": int(len(df)), "registros_validos": int(len(validos)),
        "registros_cuarentena": int(len(cuarentena)),
        "registros_por_regla": {str(k): int(v) for k, v in
                                fallas.groupby("check")["index"].nunique().items()},
    }
    return validos, cuarentena, resumen
