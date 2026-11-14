"""Orquestador del pipeline Bronce → Plata → Oro.

Uso:  python -m src.pipeline.ejecutar

Salidas
-------
data/silver/datatur_hoteles.csv          centro × categoría × mes, limpio, validado, con imputados marcados
data/silver/banxico_tipo_cambio.csv      FIX diario validado
data/silver/banxico_inpc.csv             INPC mensual validado
data/quarantine/*.csv                    registros rechazados + motivo (nunca se borran)
data/gold/destino_mes.csv                centro × mes integrado con Banxico, jerarquías, discretización,
                                         normalización y banderas de atípicos
data/gold/hotel_categoria_mes.csv        centro × categoría × mes con factores para E2
data/gold/serie_colima.csv               subconjunto Manzanillo + Colima para el pronóstico
data/gold/parametros_normalizacion.json  min, max, media y DE de cada variable normalizada
reports/E1/*.json                        evidencia de cada etapa
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import atipicos, bronce, calidad, faltantes, integracion, transformacion
from . import config as C


def _guardar_json(obj, nombre: str) -> None:
    C.REPORTES.mkdir(parents=True, exist_ok=True)
    with (C.REPORTES / nombre).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def _guardar_cuarentena(partes: list[pd.DataFrame]) -> pd.DataFrame:
    C.CUARENTENA.mkdir(parents=True, exist_ok=True)
    todas = [p.dropna(axis=1, how="all") for p in partes if len(p)]
    for f in C.CUARENTENA.glob("*.csv"):
        f.unlink()  # se regenera completa en cada corrida a partir de Bronce (Bronce nunca cambia)
    if not todas:
        return pd.DataFrame()
    q = pd.concat(todas, ignore_index=True)
    for fuente, sub in q.groupby("fuente"):
        sub.dropna(axis=1, how="all").to_csv(C.CUARENTENA / f"{fuente}_cuarentena.csv", index=False)
    return q


def main() -> int:
    inicio = datetime.now(timezone.utc)
    for d in (C.PLATA, C.ORO, C.CUARENTENA, C.REPORTES):
        d.mkdir(parents=True, exist_ok=True)
    resumen_puertas, cuarentenas = [], []

    # ---------------- 1. Bronce ----------------
    dt_raw = bronce.leer_datatur()
    tc_raw = bronce.leer_tipo_cambio()
    inpc_raw = bronce.leer_inpc()

    # ---------------- 2. Puerta 1 (entrada) ----------------
    dt_ok, dt_q, r = calidad.puerta(dt_raw, calidad.esquema_datatur("entrada"), "datatur", "1_entrada")
    resumen_puertas.append(r); cuarentenas.append(dt_q)
    tc_ok, tc_q, r = calidad.puerta(tc_raw, calidad.esquema_banxico("tipo_cambio", C.TIPO_CAMBIO_RANGO, True),
                                    "banxico_tipo_cambio", "1_entrada")
    resumen_puertas.append(r); cuarentenas.append(tc_q)
    in_ok, in_q, r = calidad.puerta(inpc_raw, calidad.esquema_banxico("inpc", C.INPC_RANGO, False),
                                    "banxico_inpc", "1_entrada")
    resumen_puertas.append(r); cuarentenas.append(in_q)

    # ---------------- 3. Faltantes ----------------
    diag = faltantes.diagnostico(dt_ok)
    dt_imp, reg_explicitos = faltantes.imputar_explicitos(dt_ok)
    dt_imp, huecos = faltantes.imputar_huecos(dt_imp)
    diag["imputaciones_explicitas"] = reg_explicitos
    diag["huecos_imputados"] = int(len(huecos))
    diag["huecos_imputados_detalle"] = (huecos[["centro", "categoria", "anio", "mes"]].to_dict("records")
                                        if len(huecos) else [])
    _guardar_json(diag, "faltantes.json")

    # ---------------- 4. Puerta 2 (Plata) ----------------
    plata, plata_q, r = calidad.puerta(dt_imp, calidad.esquema_datatur("plata"), "datatur", "2_plata")
    resumen_puertas.append(r); cuarentenas.append(plata_q)
    plata = plata.sort_values(["centro", "categoria", "anio", "mes"])
    plata.to_csv(C.PLATA / "datatur_hoteles.csv", index=False)
    tc_ok.to_csv(C.PLATA / "banxico_tipo_cambio.csv", index=False, date_format="%Y-%m-%d")
    in_ok.to_csv(C.PLATA / "banxico_inpc.csv", index=False, date_format="%Y-%m-%d")

    # ---------------- 5. Integración + reducción por agregación ----------------
    destino = integracion.agregar_destino(plata)
    oro, rep_int = integracion.integrar(destino, integracion.tipo_cambio_mensual(tc_ok),
                                        integracion.inflacion_mensual(in_ok))
    rep_int["reduccion_agregacion"] = {"registros_plata": int(len(plata)), "registros_oro": int(len(oro)),
                                       "factor": round(len(plata) / len(oro), 2)}

    # ---------------- 6. Atípicos y ruido ----------------
    oro, rep_atip = atipicos.detectar(oro, ["ocupacion_pct", "estadia_promedio"])
    _guardar_json(rep_atip, "atipicos.json")

    # ---------------- 7. Jerarquías, discretización, normalización ----------------
    oro = transformacion.agregar_jerarquias(oro)
    oro = transformacion.discretizar(oro)
    oro, params = transformacion.normalizar(oro)
    seleccion = transformacion.seleccion_variables(oro)
    rep_int["seleccion_variables"] = seleccion
    _guardar_json(rep_int, "integracion_reduccion.json")

    # ---------------- 8. Puerta 3 (Oro) ----------------
    oro, oro_q, r = calidad.puerta(oro, calidad.esquema_oro(), "oro_destino_mes", "3_oro")
    resumen_puertas.append(r); cuarentenas.append(oro_q)
    oro = oro.sort_values(["centro", "periodo"])
    oro.to_csv(C.ORO / "destino_mes.csv", index=False)
    with (C.ORO / "parametros_normalizacion.json").open("w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    # Subconjunto para pronóstico (selección de casos + variables no redundantes)
    cols_colima = (["periodo", "anio", "mes", "centro", "temporada", "periodo_covid", "choque_covid"]
                   + seleccion["seleccionadas"]
                   + ["ocupacion_pct_tratada", "ocupacion_pct_suavizada", "atipico_ocupacion_pct"])
    oro[oro["centro"].isin(["Manzanillo", "Colima"])][cols_colima].to_csv(C.ORO / "serie_colima.csv", index=False)

    # Nivel categoría para el diseño factorial de E2
    hc = transformacion.agregar_jerarquias(plata.assign(
        periodo=plata["anio"].astype(int).astype(str) + "-" + plata["mes"].astype(int).astype(str).str.zfill(2)))
    ocup = hc["cuartos_ocupados_residentes"] + hc["cuartos_ocupados_no_residentes"]
    hc["ocupacion_pct"] = (100 * ocup / hc["cuartos_disponibles"]).round(3)
    hc[["periodo", "anio", "mes", "centro", "tipo_centro", "estado", "region", "categoria", "segmento",
        "temporada", "periodo_covid", "cuartos_disponibles", "ocupacion_pct", "imputado"]
       ].to_csv(C.ORO / "hotel_categoria_mes.csv", index=False)

    # ---------------- 9. Cuarentena y reporte ----------------
    q = _guardar_cuarentena(cuarentenas)
    reporte = {
        "fecha_utc": inicio.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duracion_s": round((datetime.now(timezone.utc) - inicio).total_seconds(), 1),
        "fuentes": {"datatur": bronce.archivo_vigente("datatur"),
                    "banxico_tipo_cambio": bronce.archivo_vigente("banxico_tipo_cambio_fix"),
                    "banxico_inpc": bronce.archivo_vigente("banxico_inpc")},
        "puertas": resumen_puertas,
        "cuarentena_total": int(len(q)),
        "salidas": {"plata_datatur": int(len(plata)), "oro_destino_mes": int(len(oro)),
                    "oro_hotel_categoria_mes": int(len(hc)),
                    "oro_serie_colima": int(oro["centro"].isin(["Manzanillo", "Colima"]).sum())},
    }
    _guardar_json(reporte, "calidad.json")

    print(f"{'etapa':<12}{'fuente':<22}{'entrada':>9}{'válidos':>9}{'cuarent.':>9}")
    for p in resumen_puertas:
        print(f"{p['etapa']:<12}{p['fuente']:<22}{p['registros_entrada']:>9}{p['registros_validos']:>9}"
              f"{p['registros_cuarentena']:>9}")
    print(f"\nPlata: {len(plata)} registros · Oro: {len(oro)} destino-mes · Cuarentena: {len(q)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
