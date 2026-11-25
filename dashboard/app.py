"""Dashboard del Observatorio de Ocupación Hotelera de Colima.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python -m streamlit run dashboard/app.py

Lee exclusivamente la capa Oro (y los reportes de calidad/linaje) que genera el pipeline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.pipeline import linaje  # noqa: E402

ORO, PLATA, REP = RAIZ / "data" / "gold", RAIZ / "data" / "silver", RAIZ / "reports"
AZUL, GRIS, ROJO, NARANJA, VERDE = "#1f4e79", "#9aa5b1", "#c0504d", "#e8853d", "#5b9a68"
COLOR_GRUPO = {"Pacífico líder": VERDE, "Pacífico intermedio": AZUL, "Pacífico rezagado": ROJO}
COLOR_TIPO = {"Hotel": "#2f6fb5", "Motel": "#d9534f", "Departamento o casa amueblada": "#7fb33f",
              "Cabañas y villas": "#8e6cc2", "Pensión o casa de huéspedes": "#f0a030",
              "Campamento o albergue": "#3fb6c9"}

st.set_page_config(page_title="Observatorio Hotelero Colima", page_icon="🏨", layout="wide")


# ----------------------------------------------------------------------------- datos
@st.cache_data
def cargar():
    o = pd.read_csv(ORO / "destino_mes.csv")
    o["fecha"] = pd.to_datetime(o["periodo"])
    return {
        "oro": o,
        "mun": pd.read_csv(ORO / "municipio_hospedaje.csv", dtype={"cvegeo": str}),
        "est": pd.read_csv(ORO / "establecimientos_hospedaje.csv"),
        "calidad": json.load(open(REP / "E1" / "calidad.json", encoding="utf-8")),
        "faltantes": json.load(open(REP / "E1" / "faltantes.json", encoding="utf-8")),
        "atipicos": json.load(open(REP / "E1" / "atipicos.json", encoding="utf-8")),
        "linaje": json.load(open(REP / "E2" / "linaje.json", encoding="utf-8")),
        "bitacora": pd.read_csv(RAIZ / "data" / "bronze" / "_bitacora_captura.csv"),
        "cuarentena": pd.concat([pd.read_csv(f) for f in sorted((RAIZ / "data" / "quarantine").glob("*.csv"))],
                                ignore_index=True),
    }


@st.cache_data
def geo_municipios():
    g = gpd.read_file(PLATA / "municipios_colima.geojson")[["cvegeo", "nomgeo", "geometry"]]
    g["geometry"] = g.geometry.simplify(0.0008)  # ~90 m: suficiente para el mapa y mucho más ligero
    return json.loads(g.to_json())


@st.cache_data
def tabla_linaje():
    return pd.read_csv(linaje.ARCHIVO_LINAJE, dtype=str)


D = cargar()
oro = D["oro"]
ultimo_anio = int(oro["anio"].max())


def kpi(col, titulo, valor, delta=None, help=None):  # noqa: A002 (mismo nombre que st.metric)
    col.metric(titulo, valor, delta, help=help)


# ----------------------------------------------------------------------------- navegación
st.sidebar.title("🏨 Observatorio Hotelero")
st.sidebar.caption("Colima · Manzanillo y Colima capital")
pagina = st.sidebar.radio("Sección", ["Resumen", "Ocupación", "Comparación Pacífico", "Mapa de hospedaje",
                                      "Calidad y linaje"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown(
    f"**Datos al:** {oro['periodo'].max()}  \n"
    f"**Destinos:** {oro['centro'].nunique()} · **Registros Oro:** {len(oro):,}  \n"
    f"**Última corrida del pipeline:** {D['calidad']['fecha_utc'][:16].replace('T', ' ')} UTC"
)
st.sidebar.caption("Fuentes: SECTUR-DataTur (CC-BY 4.0) · Banco de México SIE · "
                   "INEGI, DENUE y Marco Geoestadístico. Elaboración propia.")


# ============================================================================= RESUMEN
if pagina == "Resumen":
    st.title("¿Por qué los hoteles de Manzanillo llenan sólo la mitad de sus cuartos?")
    st.caption("Indicadores clave de ocupación hotelera · fuente principal SECTUR-DataTur")

    mz = oro[oro.centro == "Manzanillo"]
    a, b = mz[mz.anio == ultimo_anio], mz[mz.anio == ultimo_anio - 1]
    ocup = lambda d: 100 * d.cuartos_ocupados.sum() / d.cuartos_disponibles.sum()
    est = lambda d: d.turistas_noche.sum() / d.llegadas.sum()
    playa = oro[(oro.tipo_centro == "Centros de Playa") & (oro.anio == ultimo_anio)]
    rank = (playa.groupby("centro")[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocup).sort_values(ascending=False).reset_index(name="ocupacion"))
    pos = int(rank.index[rank.centro == "Manzanillo"][0]) + 1

    c = st.columns(5)
    kpi(c[0], f"Ocupación Manzanillo {ultimo_anio}", f"{ocup(a):.1f} %", f"{ocup(a) - ocup(b):+.1f} pts vs {ultimo_anio - 1}")
    kpi(c[1], "Llegadas de turistas", f"{a.llegadas.sum() / 1e6:.2f} M",
        f"{100 * (a.llegadas.sum() / b.llegadas.sum() - 1):+.1f} %")
    kpi(c[2], "Estadía promedio", f"{est(a):.2f} noches", f"{est(a) - est(b):+.2f}")
    kpi(c[3], "Turistas extranjeros", f"{100 * a.llegadas_no_residentes.sum() / a.llegadas.sum():.1f} %")
    kpi(c[4], "Lugar entre centros de playa", f"{pos} de {len(rank)}", help="Por ocupación anual")

    st.subheader("Ocupación mensual: Manzanillo frente a sus pares")
    pares = oro[oro.centro.isin(["Manzanillo", "Colima", "Puerto Vallarta", "Mazatlán", "Ixtapa - Zihuatanejo"])]
    fig = px.line(pares, x="fecha", y="ocupacion_pct_suavizada", color="centro",
                  labels={"ocupacion_pct_suavizada": "Ocupación % (suavizada)", "fecha": "", "centro": ""},
                  color_discrete_map={"Manzanillo": AZUL, "Colima": NARANJA, "Puerto Vallarta": VERDE,
                                      "Mazatlán": "#8064a2", "Ixtapa - Zihuatanejo": GRIS})
    fig.add_vrect(x0="2020-03-01", x1="2021-02-28", fillcolor="#d9d9d9", opacity=.35, line_width=0,
                  annotation_text="COVID-19", annotation_position="top left")
    for tr in fig.data:
        tr.line.width = 3.2 if tr.name == "Manzanillo" else 1.6
    fig.update_layout(height=380, legend=dict(orientation="h", y=1.08), margin=dict(t=30, b=10))
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Estacionalidad de Manzanillo")
        normal = mz[mz.periodo_covid != "Pandemia"]
        s = normal.groupby("mes")[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocup).reset_index(name="ocupacion")
        s["mes_nombre"] = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        s["temporada"] = s.mes.map({4: "Alta", 7: "Alta", 8: "Alta", 12: "Alta", 9: "Baja", 10: "Baja"}).fillna("Media")
        fig = px.bar(s, x="mes_nombre", y="ocupacion", color="temporada", text_auto=".0f",
                     color_discrete_map={"Alta": VERDE, "Media": GRIS, "Baja": ROJO},
                     labels={"ocupacion": "Ocupación %", "mes_nombre": "", "temporada": "Temporada"})
        fig.update_layout(height=330, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Promedio 2016-2024 sin meses de pandemia. Septiembre es el mes más débil.")
    with c2:
        st.subheader("Llega más gente, pero se queda menos")
        anual = mz.groupby("anio").agg(llegadas=("llegadas", "sum"), noches=("turistas_noche", "sum")).reset_index()
        anual["estadia"] = anual.noches / anual.llegadas
        fig = go.Figure()
        fig.add_bar(x=anual.anio, y=anual.llegadas / 1e3, name="Llegadas (miles)", marker_color="#c6d4e1")
        fig.add_scatter(x=anual.anio, y=anual.estadia, name="Estadía (noches)", yaxis="y2",
                        line=dict(color=AZUL, width=3), mode="lines+markers")
        fig.update_layout(height=330, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.1),
                          yaxis=dict(title="Llegadas (miles)"),
                          yaxis2=dict(title="Noches", overlaying="y", side="right", rangemode="tozero"))
        st.plotly_chart(fig, width="stretch")
        st.caption("La estadía bajó de 2.75 noches (2016) a 2.0: turismo de fin de semana.")


# ============================================================================= OCUPACIÓN
elif pagina == "Ocupación":
    st.title("Explorador de ocupación hotelera")
    c1, c2, c3 = st.columns([3, 1.3, 1.3])
    destinos = c1.multiselect("Destinos", sorted(oro.centro.unique()), default=["Manzanillo", "Colima"])
    var = c2.selectbox("Indicador", {"ocupacion_pct": "Ocupación %", "estadia_promedio": "Estadía (noches)",
                                     "pct_no_residentes": "% extranjeros", "llegadas": "Llegadas"}.items(),
                       format_func=lambda x: x[1])[0]
    version = c3.radio("Serie", ["Observada", "Tratada", "Suavizada"], horizontal=False,
                       help="Tratada = atípicos sin explicación winsorizados · Suavizada = mediana móvil 3 meses")
    col = var + {"Observada": "", "Tratada": "_tratada", "Suavizada": "_suavizada"}[version] \
        if var in ("ocupacion_pct", "estadia_promedio") else var
    sel = oro[oro.centro.isin(destinos)]
    if sel.empty:
        st.info("Elige al menos un destino.")
        st.stop()
    fig = px.line(sel, x="fecha", y=col, color="centro", labels={col: "", "fecha": "", "centro": ""},
                  color_discrete_sequence=["#4f8fd6", NARANJA, VERDE, "#a98fd8", "#e0c25c", "#5fc4c4", GRIS])
    fig.add_vrect(x0="2020-03-01", x1="2021-02-28", fillcolor="#d9d9d9", opacity=.35, line_width=0,
                  annotation_text="COVID-19", annotation_position="top left")
    if var in ("ocupacion_pct", "estadia_promedio"):
        at = sel[sel[f"atipico_{var}"]]
        fig.add_scatter(x=at.fecha, y=at[var], mode="markers", name="Atípico detectado",
                        marker=dict(color=ROJO, size=7, symbol="x"),
                        text=at.centro + " · " + at.evento_conocido.fillna("sin explicación"),
                        hovertemplate="%{text}<br>%{x|%b %Y}: %{y:.1f}<extra></extra>")
    fig.update_layout(height=420, legend=dict(orientation="h", y=1.08), margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Mapa de calor mes × año")
    d1 = st.selectbox("Destino", destinos)
    piv = oro[oro.centro == d1].pivot_table(index="anio", columns="mes", values="ocupacion_pct")
    piv.columns = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][:len(piv.columns)]
    fig = px.imshow(piv, text_auto=".0f", color_continuous_scale="Blues", aspect="auto",
                    labels=dict(color="Ocupación %", x="", y=""))
    fig.update_layout(height=380, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Niveles de ocupación por temporada")
    t = oro[(oro.centro == d1) & (oro.periodo_covid != "Pandemia")]
    ct = (pd.crosstab(t.temporada, t.ocupacion_nivel, normalize="index") * 100).reindex(
        index=["Baja", "Media", "Alta"], columns=["Baja", "Media", "Alta"]).fillna(0)
    fig = px.bar(ct, orientation="h", barmode="stack", text_auto=".0f",
                 color_discrete_map={"Baja": ROJO, "Media": "#ccb974", "Alta": VERDE},
                 labels={"value": "% de meses", "temporada": "Temporada", "ocupacion_nivel": "Nivel"})
    fig.update_layout(height=260, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")


# ============================================================================= COMPARACIÓN
elif pagina == "Comparación Pacífico":
    st.title("Manzanillo frente a los destinos de playa del Pacífico")
    periodo = st.radio("Periodo", ["Pospandemia (2022-2024)", "Prepandemia (2016-2019)", "Todo"], horizontal=True)
    f = {"Pospandemia (2022-2024)": oro.periodo_covid == "Pospandemia",
         "Prepandemia (2016-2019)": oro.periodo_covid == "Prepandemia", "Todo": oro.anio > 0}[periodo]
    p = oro[f & (oro.grupo_e3 != "Otro")]
    res = p.groupby(["centro", "grupo_e3"]).agg(
        ocupacion=("ocupacion_pct", "mean"), estadia=("estadia_promedio", "mean"),
        extranjeros=("pct_no_residentes", "mean"), cuartos=("cuartos_disponibles", "mean")).reset_index()
    c1, c2 = st.columns([1.3, 1])
    with c1:
        fig = px.scatter(res, x="estadia", y="ocupacion", size="cuartos", color="grupo_e3", text="centro",
                         color_discrete_map=COLOR_GRUPO, size_max=45,
                         labels={"estadia": "Estadía promedio (noches)", "ocupacion": "Ocupación promedio %",
                                 "grupo_e3": "Grupo"})
        fig.update_traces(textposition="top center")
        fig.update_layout(height=470, legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, width="stretch")
        st.caption("Tamaño de la burbuja = cuartos disponibles por mes.")
    with c2:
        fig = px.box(p, x="grupo_e3", y="ocupacion_pct", color="grupo_e3", color_discrete_map=COLOR_GRUPO,
                     category_orders={"grupo_e3": list(COLOR_GRUPO)}, points=False,
                     labels={"grupo_e3": "", "ocupacion_pct": "Ocupación mensual %"})
        fig.update_layout(height=470, showlegend=False)
        st.plotly_chart(fig, width="stretch")
    st.dataframe(res.sort_values("ocupacion", ascending=False).round(2).rename(columns={
        "centro": "Destino", "grupo_e3": "Grupo", "ocupacion": "Ocupación %", "estadia": "Estadía",
        "extranjeros": "% extranjeros", "cuartos": "Cuartos/mes"}), hide_index=True, width="stretch")


# ============================================================================= MAPA
elif pagina == "Mapa de hospedaje":
    st.title("Oferta de hospedaje en Colima")
    st.caption("Fuente: INEGI, DENUE 05/2026 y Marco Geoestadístico dic-2025. Elaboración propia "
               "(filtro SCIAN 721, unión espacial); no representa una postura del INEGI.")
    mun, est = D["mun"], D["est"]
    c = st.columns(4)
    kpi(c[0], "Establecimientos de hospedaje", f"{len(est)}")
    kpi(c[1], "En Manzanillo", f"{100 * (est.municipio_espacial == 'Manzanillo').mean():.0f} %")
    kpi(c[2], "Micronegocios (0-10 personas)", f"{100 * (est.tamano == 'Micro').mean():.0f} %")
    kpi(c[3], "Empleo estimado", f"{int(est.personal_estimado.sum()):,}")

    tipos = st.multiselect("Tipo de alojamiento", sorted(est.tipo_alojamiento.unique()),
                           default=sorted(est.tipo_alojamiento.unique()))
    metrica = st.radio("Colorear municipios por", ["establecimientos_por_10k_hab", "establecimientos",
                                                   "establecimientos_por_100km2"], horizontal=True,
                       format_func=lambda x: {"establecimientos_por_10k_hab": "Por 10 mil habitantes",
                                              "establecimientos": "Total",
                                              "establecimientos_por_100km2": "Por 100 km²"}[x])
    fig = px.choropleth_map(mun, geojson=geo_municipios(), locations="cvegeo", featureidkey="properties.cvegeo",
                            color=metrica, color_continuous_scale="Greys", opacity=.55,
                            hover_name="nomgeo", hover_data={"cvegeo": False, "establecimientos": True,
                                                             "pct_oferta_estatal": True},
                            map_style="carto-positron", center={"lat": 19.08, "lon": -104.05}, zoom=8.3)
    e = est[est.tipo_alojamiento.isin(tipos)]
    tam = e.tamano.map({"Micro": 7, "Pequeño": 11, "Mediano": 16, "Grande": 22})
    for tipo, sub in e.groupby("tipo_alojamiento"):
        fig.add_trace(go.Scattermap(lat=sub.latitud, lon=sub.longitud, mode="markers", name=tipo,
                                    marker=dict(size=tam.loc[sub.index], opacity=.9, color=COLOR_TIPO[tipo]),
                                    text=sub.tipo_alojamiento + " · " + sub.per_ocu + " · " + sub.municipio_espacial,
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", y=-0.02, bgcolor="rgba(255,255,255,.8)"),
                      coloraxis_colorbar=dict(title="", thickness=12, len=.5))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(mun[["nomgeo", "establecimientos", "pct_oferta_estatal", "establecimientos_por_10k_hab",
                      "personal_estimado", "pct_micro", "cuartos_datatur_2024", "cuartos_por_establecimiento"]]
                 .rename(columns={"nomgeo": "Municipio", "establecimientos": "Establecimientos",
                                  "pct_oferta_estatal": "% del estado", "establecimientos_por_10k_hab": "Por 10k hab.",
                                  "personal_estimado": "Empleo est.", "pct_micro": "% micro",
                                  "cuartos_datatur_2024": "Cuartos DataTur 2024",
                                  "cuartos_por_establecimiento": "Cuartos/estab."}),
                 hide_index=True, width="stretch")


# ============================================================================= CALIDAD Y LINAJE
else:
    st.title("Calidad de datos y linaje")
    cal, lin = D["calidad"], D["linaje"]
    c = st.columns(4)
    kpi(c[0], "Registros en cuarentena", f"{cal['cuarentena_total']}", help="Nunca se borran; quedan con su motivo")
    kpi(c[1], "Huecos imputados (MAR)", f"{D['faltantes']['huecos_imputados']}",
        help=f"{D['faltantes']['huecos_por_tipo'].get('estructural', 0)} huecos estructurales sin imputar")
    kpi(c[2], "Atípicos winsorizados", f"{D['atipicos']['ocupacion_pct']['pct_winsorizado']} %")
    kpi(c[3], "Registros Oro con linaje", f"{lin['ids_oro'] - lin['registros_oro_sin_linaje']:,} / {lin['ids_oro']:,}",
        "íntegro" if lin["integro"] else "con problemas")

    t1, t2, t3 = st.tabs(["Puertas de Calidad", "Captura (Bronce)", "Rastrear un registro"])
    with t1:
        pu = pd.DataFrame(cal["puertas"])[["etapa", "fuente", "registros_entrada", "registros_validos",
                                           "registros_cuarentena"]]
        st.dataframe(pu, hide_index=True, width="stretch")
        st.markdown("**Registros en cuarentena**")
        q = D["cuarentena"]
        cols = [x for x in ["etapa", "fuente", "periodo", "anio", "mes", "centro", "categoria", "motivo"] if x in q]
        st.dataframe(q[cols], hide_index=True, width="stretch")
    with t2:
        b = D["bitacora"].sort_values("fecha_utc", ascending=False)
        st.dataframe(b[["fecha_utc", "fuente", "http", "estado", "bytes", "robots", "archivo"]].head(40),
                     hide_index=True, width="stretch")
        st.caption("Cada intento de descarga queda registrado. DataTur aparece 'bloqueado': el servidor rechaza "
                   "clientes fuera de México y el extractor no evade el bloqueo.")
    with t3:
        st.markdown("Escribe un identificador de la capa Oro y verás las filas crudas de las que salió, "
                    "con su archivo, fila y fecha de ingesta.")
        ejemplos = ["Manzanillo|2024-07", "Colima|2020-04", "municipio|06007", D["est"]["id_oro"].iloc[0]]
        c1, c2 = st.columns([2, 3])
        ej = c1.selectbox("Ejemplos", ejemplos)
        id_oro = c2.text_input("id_oro", ej, key=f"id_oro_{ej}")
        if id_oro:
            r = linaje.rastrear(id_oro.strip(), tabla_linaje(), limite=6)
            if r.empty:
                st.warning("No hay linaje para ese identificador.")
            else:
                st.dataframe(r[["fuente", "rol", "archivo_origen", "fila_origen", "fecha_ingesta"]],
                             hide_index=True, width="stretch")
                st.markdown("**Contenido crudo de las filas**")
                st.dataframe(pd.json_normalize(r["registro_crudo"].tolist()), hide_index=True,
                             width="stretch")
