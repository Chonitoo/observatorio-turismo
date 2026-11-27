"""Publicación del dataset curado (E3).

Uso:  python -m src.publicar

Genera `dataset/` a partir de la capa Oro: tablas curadas para terceros (CSV + Parquet), diccionario
de datos, `datapackage.json` (estándar Frictionless Data Package), licencia CC BY 4.0 con
atribuciones, sumas SHA-256 y una tarjeta README. Antes de escribir, cada tabla pasa por una
validación (Pandera) y por un control de privacidad: si algo falla, no se publica nada.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd
import pandera.pandas as pa

from src.pipeline import config as C
from src.pipeline import geo, integracion
from src.pipeline.io_rapido import escribir_csv

NOMBRE = "observatorio-hotelero-colima"
VERSION = "1.0.0"
DESTINO = C.RAIZ / "dataset"
REPO = "https://github.com/Chonitoo/observatorio-turismo"
AUTOR = "Maximiliano Encarnación Velázquez Rodríguez"

# ----------------------------------------------------------------------------- diccionario
# tabla → [(columna, tipo, unidad, descripción)]
DICCIONARIO = {
    "ocupacion_destino_mes": [
        ("id_registro", "string", "", "Identificador único: '<destino>|<AAAA-MM>'. Permite rastrear el registro en el repositorio (linaje)."),
        ("periodo", "string", "AAAA-MM", "Mes de referencia en formato año-mes."),
        ("anio", "integer", "año", "Año calendario del registro."),
        ("mes", "integer", "1-12", "Mes calendario (1 = enero, 12 = diciembre)."),
        ("destino", "string", "", "Centro turístico monitoreado por DataTur (64 destinos)."),
        ("estado", "string", "", "Entidad federativa del destino."),
        ("region", "string", "", "Región económica (regionalización del Banco de México): Norte, Centro Norte, Centro, Sur."),
        ("tipo_destino", "string", "", "Centros de Playa o Ciudades (clasificación DataTur)."),
        ("subtipo_destino", "string", "", "Subclasificación DataTur (Integralmente Planeados, Tradicionales, Interior, Fronterizas, etc.)."),
        ("litoral", "string", "", "Pacífico, Golfo-Caribe o 'No aplica' (ciudades)."),
        ("temporada", "string", "", "Alta (abr, jul, ago, dic), Media o Baja (sep, oct)."),
        ("periodo_covid", "string", "", "Prepandemia (hasta feb-2020), Pandemia (mar-2020 a dic-2021) o Pospandemia."),
        ("cuartos_disponibles", "number", "cuartos-noche", "Oferta del mes: suma de cuartos disponibles por noche de las categorías reportadas."),
        ("cuartos_ocupados", "number", "cuartos-noche", "Cuartos ocupados (residentes + no residentes)."),
        ("llegadas", "number", "personas", "Llegadas de turistas (residentes + no residentes)."),
        ("llegadas_extranjeros", "number", "personas", "Llegadas de turistas no residentes en México."),
        ("turistas_noche", "number", "personas-noche", "Turistas-noche (residentes + no residentes)."),
        ("ocupacion_pct", "number", "%", "Ocupación hotelera = cuartos ocupados / cuartos disponibles × 100."),
        ("ocupacion_pct_tratada", "number", "%", "Ocupación con los atípicos sin explicación winsorizados (los choques reales se conservan)."),
        ("ocupacion_nivel", "string", "", "Discretización: Baja (<40 %), Media (40-60 %), Alta (≥60 %)."),
        ("estadia_promedio", "number", "noches", "Turistas-noche / llegadas. Vacío si no hubo llegadas."),
        ("densidad", "number", "personas por cuarto", "Turistas-noche / cuartos ocupados. Vacío si no hubo ocupación."),
        ("pct_extranjeros", "number", "%", "Llegadas de no residentes / llegadas × 100."),
        ("atipico", "boolean", "", "Atípico por consenso IQR + Z-score robusto sobre el residuo sin tendencia ni estacionalidad."),
        ("evento_conocido", "string", "", "Choque exógeno conocido en ese mes (pandemia COVID-19, huracán Otis), si aplica."),
        ("categorias_reportadas", "integer", "", "Número de categorías hoteleras (1★-5★, sin categoría) reportadas ese mes."),
        ("registros_imputados", "integer", "", "Cuántas de esas categorías fueron imputadas (huecos internos ≤ 3 meses)."),
        ("pct_oferta_imputada", "number", "%", "Porcentaje de los cuartos disponibles que proviene de registros imputados."),
        ("tipo_cambio", "number", "MXN por USD", "Promedio mensual del tipo de cambio FIX (Banco de México, serie SF43718)."),
        ("inflacion_anual_pct", "number", "%", "Variación anual del INPC (Banco de México, serie SP1)."),
        ("fecha_ingesta", "string", "UTC ISO 8601", "Fecha en que el archivo crudo de DataTur entró al repositorio."),
    ],
    "ocupacion_categoria_mes": [
        ("id_registro", "string", "", "Identificador único: 'hc|<destino>|<categoría>|<AAAA-MM>'."),
        ("periodo", "string", "AAAA-MM", "Mes de referencia en formato año-mes."),
        ("anio", "integer", "año", "Año calendario del registro."),
        ("mes", "integer", "1-12", "Mes calendario (1 = enero, 12 = diciembre)."),
        ("destino", "string", "", "Centro turístico DataTur."),
        ("tipo_destino", "string", "", "Centros de Playa o Ciudades."),
        ("estado", "string", "", "Entidad federativa."),
        ("region", "string", "", "Región económica (Banco de México)."),
        ("categoria", "string", "", "Categoría hotelera: 1 estrella … 5 estrellas, Sin categoría."),
        ("segmento", "string", "", "Económico (1-2★), Medio (3★), Superior (4-5★), Sin clasificar."),
        ("temporada", "string", "", "Alta, Media o Baja."),
        ("periodo_covid", "string", "", "Prepandemia, Pandemia o Pospandemia."),
        ("cuartos_disponibles", "number", "cuartos-noche", "Cuartos disponibles por noche en el mes."),
        ("ocupacion_pct", "number", "%", "Ocupación de la categoría en el mes."),
        ("imputado", "boolean", "", "True si el registro fue imputado (hueco interno ≤ 3 meses; nunca en meses de pandemia)."),
        ("id_bronce", "string", "", "Identificador del registro crudo de origen ('IMPUTADO:…' si fue imputado)."),
    ],
    "hospedaje_establecimientos": [
        ("id_registro", "string", "", "Identificador: 'denue|<id DENUE>'."),
        ("id_denue", "string", "", "Identificador del establecimiento en el DENUE (INEGI)."),
        ("clee", "string", "", "Clave Única del Establecimiento (INEGI)."),
        ("codigo_scian", "string", "", "Código SCIAN 2023 de la actividad (721xxx = alojamiento temporal)."),
        ("actividad", "string", "", "Nombre de la actividad SCIAN."),
        ("tipo_alojamiento", "string", "", "Hotel, Motel, Departamento o casa amueblada, Cabañas y villas, Pensión o casa de huéspedes, Campamento o albergue."),
        ("estrato_personal", "string", "personas", "Estrato de personal ocupado declarado en el DENUE."),
        ("tamano", "string", "", "Micro (0-10), Pequeño (11-50), Mediano (51-250), Grande (251+)."),
        ("personal_estimado", "integer", "personas", "Punto medio del estrato (aproximación)."),
        ("clave_municipio", "string", "", "Clave geoestadística del municipio donde cae el punto (unión espacial)."),
        ("municipio", "string", "", "Municipio donde cae el punto."),
        ("localidad", "string", "", "Localidad declarada en el DENUE."),
        ("latitud", "number", "grados (WGS84)", "Latitud del establecimiento."),
        ("longitud", "number", "grados (WGS84)", "Longitud del establecimiento."),
        ("anio_alta", "integer", "año", "Año de alta en el DENUE (NO es el año de apertura)."),
        ("municipio_coincide", "boolean", "", "False si el municipio declarado difiere del municipio donde cae el punto."),
    ],
    "hospedaje_municipios": [
        ("id_registro", "string", "", "Identificador: 'municipio|<clave>'."),
        ("clave_municipio", "string", "", "Clave geoestadística INEGI (06001-06010)."),
        ("municipio", "string", "", "Nombre del municipio."),
        ("poblacion_2020", "integer", "personas", "Población total (Censo de Población y Vivienda 2020)."),
        ("area_km2", "number", "km²", "Área del municipio (Marco Geoestadístico, proyección EPSG:6372)."),
        ("establecimientos", "integer", "", "Establecimientos de hospedaje (SCIAN 721) en el municipio."),
        ("pct_oferta_estatal", "number", "%", "Porcentaje de los establecimientos del estado."),
        ("establecimientos_por_10k_hab", "number", "por 10 mil habitantes", "Densidad por población."),
        ("establecimientos_por_100km2", "number", "por 100 km²", "Densidad por superficie."),
        ("personal_estimado", "integer", "personas", "Suma del personal estimado."),
        ("pct_micro", "number", "%", "Porcentaje de micronegocios (0-10 personas)."),
        ("hoteles", "integer", "", "Establecimientos tipo hotel (SCIAN 721111 y 721112)."),
        ("moteles", "integer", "", "Moteles (721113)."),
        ("departamentos_casas", "integer", "", "Departamentos y casas amueblados con servicios de hotelería (721312)."),
        ("cabanas_villas", "integer", "", "Cabañas, villas y similares (721190)."),
        ("pensiones", "integer", "", "Pensiones y casas de huéspedes (721311)."),
        ("cuartos_datatur_2024", "number", "cuartos por noche", "Promedio de cuartos por noche reportados a DataTur en 2024 (sólo Manzanillo y Colima)."),
    ],
    "indicadores_macro_mes": [
        ("periodo", "string", "AAAA-MM", "Mes de referencia en formato año-mes."),
        ("tipo_cambio", "number", "MXN por USD", "Promedio mensual del FIX (SF43718)."),
        ("tipo_cambio_cierre", "number", "MXN por USD", "Último FIX publicado en el mes."),
        ("dias_cotizados", "integer", "días", "Días hábiles con cotización."),
        ("inpc", "number", "índice (2Q jul-2018 = 100)", "Índice Nacional de Precios al Consumidor (SP1)."),
        ("inflacion_anual_pct", "number", "%", "Variación del INPC respecto al mismo mes del año anterior."),
    ],
}

DESCRIPCION_TABLA = {
    "ocupacion_destino_mes": "Ocupación hotelera mensual por destino turístico (64 destinos, 2016-2024), integrada con tipo de cambio e inflación.",
    "ocupacion_categoria_mes": "Ocupación hotelera mensual por destino y categoría (1★-5★), para análisis de factores.",
    "hospedaje_establecimientos": "Establecimientos de hospedaje de Colima (DENUE 2026) con ubicación, tipo y tamaño. Sin datos de contacto.",
    "hospedaje_municipios": "Oferta de hospedaje por municipio de Colima con densidades por población y superficie.",
    "indicadores_macro_mes": "Tipo de cambio FIX e inflación anual (INPC) mensuales.",
}

PROHIBIDAS = set(geo.COLS_DESCARTADAS_PRIVACIDAD)


# ----------------------------------------------------------------------------- construcción
def construir_tablas() -> dict[str, pd.DataFrame]:
    o = pd.read_csv(C.ORO / "destino_mes.csv", low_memory=False)
    destino = o.rename(columns={
        "id_oro": "id_registro", "centro": "destino", "tipo_centro": "tipo_destino",
        "subtipo_centro": "subtipo_destino", "llegadas_no_residentes": "llegadas_extranjeros",
        "pct_no_residentes": "pct_extranjeros", "atipico_ocupacion_pct": "atipico",
        "fecha_ingesta_datatur": "fecha_ingesta"})
    destino["evento_conocido"] = destino["evento_conocido"].fillna("")

    hc = pd.read_csv(C.ORO / "hotel_categoria_mes.csv", low_memory=False).rename(columns={
        "id_oro": "id_registro", "centro": "destino", "tipo_centro": "tipo_destino"})

    est = pd.read_csv(C.ORO / "establecimientos_hospedaje.csv", dtype={"id": str, "clee": str,
                                                                        "codigo_act": str, "cvegeo_espacial": str})
    est = est.rename(columns={"id_oro": "id_registro", "id": "id_denue", "codigo_act": "codigo_scian",
                              "nombre_act": "actividad", "per_ocu": "estrato_personal",
                              "cvegeo_espacial": "clave_municipio", "municipio_espacial": "municipio_x"})
    est = est.drop(columns="municipio").rename(columns={"municipio_x": "municipio"})

    mun = pd.read_csv(C.ORO / "municipio_hospedaje.csv", dtype={"cvegeo": str}).rename(columns={
        "id_oro": "id_registro", "cvegeo": "clave_municipio", "nomgeo": "municipio", "pob_total": "poblacion_2020",
        "n_Hotel": "hoteles", "n_Motel": "moteles", "n_Departamento o casa amueblada": "departamentos_casas",
        "n_Cabañas y villas": "cabanas_villas", "n_Pensión o casa de huéspedes": "pensiones"})

    tc = pd.read_csv(C.PLATA / "banxico_tipo_cambio.csv", parse_dates=["fecha"])
    inpc = pd.read_csv(C.PLATA / "banxico_inpc.csv", parse_dates=["fecha"])
    macro = integracion.tipo_cambio_mensual(tc).merge(integracion.inflacion_mensual(inpc), on="periodo", how="outer")

    tablas = {"ocupacion_destino_mes": destino, "ocupacion_categoria_mes": hc, "hospedaje_establecimientos": est,
              "hospedaje_municipios": mun, "indicadores_macro_mes": macro}
    return {t: df[[c for c, *_ in DICCIONARIO[t]]].copy() for t, df in tablas.items()}


def validar(tablas: dict[str, pd.DataFrame]) -> dict:
    pct = pa.Check.in_range(0, 100)
    esquemas = {
        "ocupacion_destino_mes": pa.DataFrameSchema({
            "id_registro": pa.Column(str, unique=True), "periodo": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}$")),
            "ocupacion_pct": pa.Column(float, pct), "pct_extranjeros": pa.Column(float, pct, nullable=True),
            "estadia_promedio": pa.Column(float, pa.Check.in_range(1, 30), nullable=True),
            "tipo_cambio": pa.Column(float, pa.Check.in_range(*C.TIPO_CAMBIO_RANGO))}),
        "ocupacion_categoria_mes": pa.DataFrameSchema({
            "id_registro": pa.Column(str, unique=True), "ocupacion_pct": pa.Column(float, pct),
            "categoria": pa.Column(str, pa.Check.isin(C.CATEGORIAS))}),
        "hospedaje_establecimientos": pa.DataFrameSchema({
            "id_registro": pa.Column(str, unique=True),
            "latitud": pa.Column(float, pa.Check.in_range(*geo.BBOX_COLIMA["lat"])),
            "longitud": pa.Column(float, pa.Check.in_range(*geo.BBOX_COLIMA["lon"]))}),
        "hospedaje_municipios": pa.DataFrameSchema({
            "clave_municipio": pa.Column(str, unique=True), "pct_oferta_estatal": pa.Column(float, pct)}),
        "indicadores_macro_mes": pa.DataFrameSchema({"periodo": pa.Column(str, unique=True)}),
    }
    for t, df in tablas.items():
        esquemas[t].validate(df, lazy=True)
        fuga = PROHIBIDAS & set(df.columns)
        assert not fuga, f"{t}: columnas personales {fuga}"
    return {t: int(len(df)) for t, df in tablas.items()}


def _sha256(ruta) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _tipo_frictionless(t: str) -> str:
    return {"string": "string", "integer": "integer", "number": "number", "boolean": "boolean"}[t]


def publicar() -> dict:
    tablas = construir_tablas()
    filas = validar(tablas)

    tmp = DESTINO.with_name("dataset.tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "parquet").mkdir(parents=True)
    for t, df in tablas.items():
        escribir_csv(df, tmp / f"{t}.csv")
        df.to_parquet(tmp / "parquet" / f"{t}.parquet", index=False)

    dic = pd.DataFrame([(t, c, ty, u, d) for t, cols in DICCIONARIO.items() for c, ty, u, d in cols],
                       columns=["tabla", "columna", "tipo", "unidad", "descripcion"])
    dic.to_csv(tmp / "diccionario_datos.csv", index=False)

    ahora = datetime.now(timezone.utc)
    paquete = {
        "profile": "tabular-data-package",
        "name": NOMBRE, "version": VERSION,
        "title": "Observatorio de Ocupación Hotelera de Colima — dataset curado",
        "description": ("Ocupación hotelera mensual de 64 destinos turísticos de México (2016-2024) con énfasis en "
                        "Colima (Manzanillo y Colima capital), integrada con tipo de cambio e inflación, y oferta de "
                        "hospedaje georreferenciada de Colima. Datos limpios, validados y trazables."),
        "homepage": REPO,
        "created": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "contributors": [{"title": AUTOR, "role": "author"}],
        "keywords": ["turismo", "ocupación hotelera", "Colima", "Manzanillo", "DataTur", "DENUE", "México"],
        "licenses": [{"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0",
                      "path": "https://creativecommons.org/licenses/by/4.0/"}],
        "sources": [
            {"title": "SECTUR, DataTur: Ocupación hotelera en los 70 destinos principales (CC-BY 4.0)",
             "path": "https://www.datos.gob.mx/dataset/ocupacion_hotelera_70_destinos_principales_monitoreados_datatur"},
            {"title": "Banco de México, Sistema de Información Económica: SF43718 (FIX) y SP1 (INPC)",
             "path": "https://www.banxico.org.mx/SieAPIRest/service/v1/"},
            {"title": "INEGI, Directorio Estadístico Nacional de Unidades Económicas (DENUE) 05/2026",
             "path": "https://www.inegi.org.mx/app/descarga/?ti=6"},
            {"title": "INEGI, Marco Geoestadístico dic-2025; Censo de Población y Vivienda 2020",
             "path": "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06"},
        ],
        "resources": [],
    }
    for t, df in tablas.items():
        ruta = tmp / f"{t}.csv"
        paquete["resources"].append({
            "profile": "tabular-data-resource",
            "name": t, "path": f"{t}.csv", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
            "description": DESCRIPCION_TABLA[t], "bytes": ruta.stat().st_size, "hash": f"sha256:{_sha256(ruta)}",
            "rows": filas[t],
            "schema": {"fields": [{"name": c, "type": _tipo_frictionless(ty), "description": d,
                                   **({"unit": u} if u else {})} for c, ty, u, d in DICCIONARIO[t]],
                       **({"primaryKey": ["id_registro"]} if "id_registro" in df.columns
                          else {"primaryKey": ["periodo"]})},
        })
    (tmp / "datapackage.json").write_text(json.dumps(paquete, ensure_ascii=False, indent=2), encoding="utf-8")

    (tmp / "LICENSE.md").write_text(f"""# Licencia

Este dataset se publica bajo **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**:
https://creativecommons.org/licenses/by/4.0/deed.es

Puedes copiarlo, redistribuirlo, transformarlo y usarlo con cualquier fin, incluso comercial, siempre que
des el crédito correspondiente:

> {AUTOR} ({ahora.year}). *Observatorio de Ocupación Hotelera de Colima — dataset curado* (v{VERSION}).
> {REPO}

## Atribución de las fuentes originales

- **SECTUR, DataTur**: *Ocupación hotelera en los 70 destinos principales monitoreados*, datos.gob.mx, CC BY 4.0.
- **Banco de México**: Sistema de Información Económica (SIE), series SF43718 y SP1.
- **Fuente: INEGI**, Directorio Estadístico Nacional de Unidades Económicas (DENUE) 05/2026, y Marco
  Geoestadístico dic-2025 / Censo de Población y Vivienda 2020 (Términos de Libre Uso de la Información del INEGI).

Este dataset es **elaboración propia**: los datos fueron limpiados, validados, imputados (cuando se indica),
agregados e integrados. No representa una postura oficial de SECTUR, Banco de México ni INEGI, ni implica su aval.
""", encoding="utf-8")

    sumas = [f"{_sha256(f)}  {f.relative_to(tmp).as_posix()}" for f in sorted(tmp.rglob("*"))
             if f.is_file() and f.name != "SHA256SUMS.txt"]
    (tmp / "SHA256SUMS.txt").write_text("\n".join(sumas) + "\n", encoding="utf-8")

    tabla_md = "\n".join(f"| `{t}.csv` | {filas[t]:,} | {len(DICCIONARIO[t])} | {DESCRIPCION_TABLA[t]} |" for t in tablas)
    (tmp / "README.md").write_text(f"""# Observatorio de Ocupación Hotelera de Colima — dataset curado

**Versión {VERSION}** · Licencia **CC BY 4.0** · Generado automáticamente desde la capa Oro del observatorio.

| Archivo | Filas | Columnas | Contenido |
|---|---:|---:|---|
{tabla_md}

- `parquet/`: las mismas tablas en formato Parquet (tipos preservados, más ligeras).
- `diccionario_datos.csv`: descripción, tipo y unidad de cada columna.
- `datapackage.json`: metadatos estándar ([Frictionless Data Package](https://datapackage.org/)).
- `SHA256SUMS.txt`: huellas para verificar la integridad de cada archivo.
- **Ficha técnica completa (datasheet):** [`docs/E3/datasheet.md`]({REPO}/blob/main/docs/E3/datasheet.md).

## Carga rápida

```python
import pandas as pd
base = "https://raw.githubusercontent.com/Chonitoo/observatorio-turismo/main/dataset/"
ocupacion = pd.read_csv(base + "ocupacion_destino_mes.csv")
```

## Cita

{AUTOR} ({ahora.year}). *Observatorio de Ocupación Hotelera de Colima — dataset curado* (v{VERSION}). {REPO}
""", encoding="utf-8")

    shutil.rmtree(DESTINO, ignore_errors=True)
    tmp.rename(DESTINO)
    return {"version": VERSION, "filas": filas,
            "bytes_csv": sum(f.stat().st_size for f in DESTINO.glob("*.csv")),
            "bytes_parquet": sum(f.stat().st_size for f in (DESTINO / "parquet").glob("*.parquet"))}


if __name__ == "__main__":
    r = publicar()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0)
