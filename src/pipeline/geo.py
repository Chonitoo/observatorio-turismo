"""Fuente especializada geoespacial: oferta de hospedaje en Colima (DENUE + Marco Geoestadístico).

Flujo
-----
Bronce  denue_06_csv_*.zip (todo Colima, 42 mil establecimientos)  +  mgem_06_colima_*.geojson
  │  filtro SCIAN 721 (alojamiento temporal) y MINIMIZACIÓN: se descartan nombre, razón social,
  │  teléfono, correo, página web y domicilio (no se necesitan para el análisis y pueden
  │  identificar a personas físicas dueñas de negocios pequeños)
  ▼
[Puerta G1 · entrada]  esquema, dominio SCIAN, estrato de personal, coordenadas válidas
  │  unión espacial (GeoPandas, EPSG:6372) punto → municipio; consistencia con el municipio declarado
  ▼
[Puerta G2 · Plata]    el punto debe caer dentro de Colima (tolerancia costera de 1 km)
  ▼
Plata   denue_hospedaje_colima.csv · municipios_colima.geojson
  ▼
Oro     establecimientos_hospedaje.csv (un registro por establecimiento)
        municipio_hospedaje.csv (oferta por municipio, por tipo y tamaño, densidad por habitantes y km²)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.pandas as pa

from . import calidad
from . import config as C

CRS_METROS = 6372   # Lambert Conformal Conic de México (INEGI): áreas y distancias en metros

SCIAN_TIPO = {
    "721111": "Hotel", "721112": "Hotel", "721113": "Motel",
    "721190": "Cabañas y villas", "721210": "Campamento o albergue",
    "721311": "Pensión o casa de huéspedes", "721312": "Departamento o casa amueblada",
}
PER_OCU = {  # estrato de personal ocupado → (tamaño, punto medio para estimar empleo)
    "0 a 5 personas": ("Micro", 3), "6 a 10 personas": ("Micro", 8),
    "11 a 30 personas": ("Pequeño", 20), "31 a 50 personas": ("Pequeño", 40),
    "51 a 100 personas": ("Mediano", 75), "101 a 250 personas": ("Mediano", 175),
    "251 y más personas": ("Grande", 300),
}
COLS_CONSERVADAS = ["id", "clee", "codigo_act", "nombre_act", "per_ocu", "cve_ent", "cve_mun",
                    "municipio", "cve_loc", "localidad", "tipoUniEco", "latitud", "longitud", "fecha_alta"]
COLS_DESCARTADAS_PRIVACIDAD = ["nom_estab", "raz_social", "telefono", "correoelec", "www", "tipo_vial",
                               "nom_vial", "numero_ext", "numero_int", "letra_ext", "letra_int",
                               "edificio", "edificio_e", "nomb_asent", "manzana"]
BBOX_COLIMA = {"lat": (18.6, 19.6), "lon": (-104.8, -103.4)}   # territorio continental
CENTRO_DATATUR_MUN = {"Manzanillo": "06007", "Colima": "06002"}


def minimizar(denue: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    from .bronce import COLS_LINAJE
    quitadas = [c for c in COLS_DESCARTADAS_PRIVACIDAD if c in denue.columns]
    return denue[COLS_LINAJE + [c for c in COLS_CONSERVADAS if c in denue.columns]].copy(), quitadas


def esquema_denue() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "id": pa.Column(str, pa.Check.str_matches(r"^\d+$", error="id DENUE no numérico")),
            "codigo_act": pa.Column(str, pa.Check.isin(list(SCIAN_TIPO), error="SCIAN fuera de alojamiento 721")),
            "per_ocu": pa.Column(str, pa.Check.isin(list(PER_OCU), error="estrato de personal desconocido")),
            "cve_ent": pa.Column(str, pa.Check.eq("06", error="entidad distinta de Colima")),
            "cve_mun": pa.Column(str, pa.Check.str_matches(r"^0(0[1-9]|10)$", error="municipio fuera de 001-010")),
            "latitud": pa.Column(float, pa.Check.in_range(*BBOX_COLIMA["lat"], error="latitud fuera de Colima")),
            "longitud": pa.Column(float, pa.Check.in_range(*BBOX_COLIMA["lon"], error="longitud fuera de Colima")),
            "fecha_alta": pa.Column(str, pa.Check.str_matches(r"^(19|20)\d{2}-(0[1-9]|1[0-2])$",
                                                              error="fecha_alta no es AAAA-MM")),
        },
        checks=[pa.Check(lambda d: ~d["id"].duplicated(keep=False), error="G-R1: id DENUE duplicado")],
        coerce=True, name="denue_hospedaje",
    )


def esquema_denue_plata() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {"cvegeo_espacial": pa.Column(str, nullable=False),
         "distancia_colima_m": pa.Column(float, pa.Check.le(1000, error="G-R2: punto a más de 1 km de Colima"))},
        coerce=True, name="denue_hospedaje_plata",
    )


def union_espacial(denue: pd.DataFrame, municipios):
    """Asigna a cada establecimiento el municipio que contiene su punto (o el más cercano si cae
    en el mar a menos de 1 km por la generalización de la línea de costa)."""
    import geopandas as gpd
    pts = gpd.GeoDataFrame(denue, geometry=gpd.points_from_xy(denue["longitud"], denue["latitud"]),
                           crs=4326).to_crs(CRS_METROS)
    mun = municipios[["cvegeo", "nomgeo", "geometry"]].to_crs(CRS_METROS)
    j = gpd.sjoin_nearest(pts, mun, how="left", distance_col="distancia_colima_m")
    j = j[~j.index.duplicated(keep="first")]
    j = j.rename(columns={"cvegeo": "cvegeo_espacial", "nomgeo": "municipio_espacial"})
    j["municipio_coincide"] = (j["cve_ent"] + j["cve_mun"]) == j["cvegeo_espacial"]
    return pd.DataFrame(j.drop(columns=["geometry", "index_right"]))


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["tipo_alojamiento"] = d["codigo_act"].map(SCIAN_TIPO)
    d["tamano"] = d["per_ocu"].map(lambda x: PER_OCU[x][0])
    d["personal_estimado"] = d["per_ocu"].map(lambda x: PER_OCU[x][1])
    d["anio_alta"] = d["fecha_alta"].str[:4].astype(int)
    d.insert(0, "id_oro", "denue|" + d["id"])
    return d


def municipal(est: pd.DataFrame, municipios) -> pd.DataFrame:
    mun = municipios.to_crs(CRS_METROS).copy()
    mun["area_km2"] = (mun.geometry.area / 1e6).round(1)
    base = pd.DataFrame(mun.drop(columns="geometry"))[["cvegeo", "nomgeo", "pob_total", "area_km2"]]
    g = est.groupby("cvegeo_espacial")
    agg = pd.DataFrame({
        "establecimientos": g.size(),
        "personal_estimado": g["personal_estimado"].sum(),
        "pct_micro": g["tamano"].apply(lambda s: round(100 * (s == "Micro").mean(), 1)),
        "anio_alta_mediana": g["anio_alta"].median(),
    })
    por_tipo = pd.crosstab(est["cvegeo_espacial"], est["tipo_alojamiento"]).add_prefix("n_")
    por_tamano = pd.crosstab(est["cvegeo_espacial"], est["tamano"]).add_prefix("n_")
    out = base.merge(agg.join(por_tipo).join(por_tamano), left_on="cvegeo", right_index=True, how="left")
    num = out.columns.difference(["cvegeo", "nomgeo", "anio_alta_mediana"])
    out[num] = out[num].fillna(0)
    out["establecimientos_por_10k_hab"] = (1e4 * out["establecimientos"] / out["pob_total"]).round(2)
    out["establecimientos_por_100km2"] = (100 * out["establecimientos"] / out["area_km2"]).round(2)
    out["pct_oferta_estatal"] = (100 * out["establecimientos"] / out["establecimientos"].sum()).round(1)
    out.insert(0, "id_oro", "municipio|" + out["cvegeo"])
    return out.sort_values("establecimientos", ascending=False)


def cuartos_datatur(plata_datatur: pd.DataFrame, anio: int = 2024) -> pd.DataFrame:
    """Cuartos promedio por noche reportados a DataTur (para contrastar con DENUE)."""
    d = plata_datatur[(plata_datatur["anio"] == anio) & plata_datatur["centro"].isin(CENTRO_DATATUR_MUN)].copy()
    d["dias"] = pd.to_datetime(dict(year=d["anio"], month=d["mes"], day=1)).dt.days_in_month
    d["cuartos_noche"] = d["cuartos_disponibles"] / d["dias"]
    m = d.groupby(["centro", "mes"])["cuartos_noche"].sum().groupby("centro").mean().round(0)
    return pd.DataFrame({"cvegeo": [CENTRO_DATATUR_MUN[c] for c in m.index],
                         f"cuartos_datatur_{anio}": m.values})


def ejecutar(plata_datatur: pd.DataFrame) -> dict:
    """Corre la rama geoespacial completa y devuelve tablas + reportes."""
    from . import bronce
    import geopandas as gpd

    municipios = bronce.leer_municipios()
    crudo = bronce.leer_denue()
    denue, quitadas = minimizar(crudo)

    ok, q1, r1 = calidad.puerta(denue, esquema_denue(), "inegi_denue_colima", "G1_entrada")
    unido = union_espacial(ok, municipios)
    plata, q2, r2 = calidad.puerta(unido, esquema_denue_plata(), "inegi_denue_colima", "G2_plata")
    est = enriquecer(plata)
    mun = municipal(est, municipios).merge(cuartos_datatur(plata_datatur), on="cvegeo", how="left")
    mun["cuartos_por_establecimiento"] = (mun["cuartos_datatur_2024"] / mun["establecimientos"]).round(1)

    # Linaje: municipio → establecimientos DENUE (unión espacial) + polígono/población del Marco
    lin_est = est.assign(tabla_oro="establecimientos_hospedaje", fuente="inegi_denue_colima",
                         rol="registro DENUE (columnas personales descartadas)")
    lin_mun_d = est.assign(id_oro="municipio|" + est["cvegeo_espacial"], tabla_oro="municipio_hospedaje",
                           fuente="inegi_denue_colima", rol="conteo por unión espacial punto→municipio")
    mg = pd.DataFrame(municipios.drop(columns="geometry"))
    lin_mun_m = mg.assign(id_oro="municipio|" + mg["cvegeo"], tabla_oro="municipio_hospedaje",
                          fuente="inegi_mg_municipios", rol="polígono, área y población (Censo 2020)")
    cols = ["id_oro", "tabla_oro", "fuente", "id_bronce", "archivo_origen", "fila_origen",
            "sha256_bronce", "fecha_ingesta", "rol"]
    linaje = pd.concat([x[cols] for x in (lin_est, lin_mun_d, lin_mun_m)], ignore_index=True)

    resumen = {
        "archivo_denue": bronce.archivo_vigente("inegi_denue_colima"),
        "archivo_marco_geoestadistico": bronce.archivo_vigente("inegi_mg_municipios"),
        "denue_hospedaje_bronce": int(len(crudo)),
        "columnas_descartadas_por_privacidad": quitadas,
        "puertas": [r1, r2],
        "municipio_no_coincide": int((~est["municipio_coincide"]).sum()),
        "ejemplos_no_coincide": est.loc[~est["municipio_coincide"],
                                        ["id", "municipio", "municipio_espacial", "distancia_colima_m"]]
        .round(0).head(10).to_dict("records"),
        "por_tipo": est["tipo_alojamiento"].value_counts().to_dict(),
        "por_tamano": est["tamano"].value_counts().to_dict(),
    }
    return {"plata": plata, "municipios": municipios, "establecimientos": est, "municipal": mun,
            "cuarentena": [q1, q2], "puertas": [r1, r2], "linaje": linaje, "resumen": resumen}
