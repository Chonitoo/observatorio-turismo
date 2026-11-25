"""Tablero del Observatorio de Ocupación Hotelera de Colima — versión para el cliente.

Pensado para hoteleros y para la Secretaría de Turismo: cada sección responde una pregunta de
negocio en lenguaje simple, con la conclusión escrita arriba de cada gráfica.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python -m streamlit run dashboard/app.py
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
AZUL, ROJO, NARANJA, VERDE, AMARILLO = "#2f6fb5", "#d9534f", "#e8853d", "#4fa36a", "#e0b84c"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
               "octubre", "noviembre", "diciembre"]
COLOR_TIPO = {"Hotel": "#2f6fb5", "Motel": "#d9534f", "Departamento o casa amueblada": "#7fb33f",
              "Cabañas y villas": "#8e6cc2", "Pensión o casa de huéspedes": "#f0a030",
              "Campamento o albergue": "#3fb6c9"}

st.set_page_config(page_title="Observatorio Hotelero de Colima", page_icon="🏨", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2.2rem; max-width: 1250px;}
div[data-testid="stMetricValue"] {font-size: 1.9rem;}
.tarjeta {border: 1px solid rgba(128,128,128,.35); border-radius: 12px; padding: 14px 16px; margin-bottom: 6px;}
.tarjeta h4 {margin: 0 0 6px 0; font-size: 1.02rem;}
.tarjeta p {margin: 0; opacity: .85; font-size: .93rem;}
</style>""", unsafe_allow_html=True)


# ============================================================================= datos
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
        "linaje": json.load(open(REP / "E2" / "linaje.json", encoding="utf-8")),
        "bitacora": pd.read_csv(RAIZ / "data" / "bronze" / "_bitacora_captura.csv"),
        "cuarentena": pd.concat([pd.read_csv(f) for f in sorted((RAIZ / "data" / "quarantine").glob("*.csv"))],
                                ignore_index=True),
    }


@st.cache_data
def geo_municipios():
    g = gpd.read_file(PLATA / "municipios_colima.geojson")[["cvegeo", "nomgeo", "geometry"]]
    g["geometry"] = g.geometry.simplify(0.0008)
    return json.loads(g.to_json())


@st.cache_data
def tabla_linaje():
    return pd.read_csv(linaje.ARCHIVO_LINAJE, dtype=str)


D = cargar()
oro = D["oro"]
ANIO_MAX = int(oro["anio"].max())
NORMAL = oro["periodo_covid"] != "Pandemia"


def ocupacion(d: pd.DataFrame) -> float:
    """Ocupación ponderada: cuartos ocupados / cuartos disponibles (no promedio de porcentajes)."""
    return 100 * d["cuartos_ocupados"].sum() / d["cuartos_disponibles"].sum()


def estadia(d: pd.DataFrame) -> float:
    return d["turistas_noche"].sum() / d["llegadas"].sum()


def extranjeros(d: pd.DataFrame) -> float:
    return 100 * d["llegadas_no_residentes"].sum() / d["llegadas"].sum()


def por_mes(d: pd.DataFrame) -> pd.Series:
    return d.groupby("mes")[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocupacion)


def resumen_por(d: pd.DataFrame, col: str) -> pd.DataFrame:
    g = d.groupby(col)
    return pd.DataFrame({
        "ocupacion": g[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocupacion),
        "estadia": g[["turistas_noche", "llegadas"]].apply(estadia),
        "extranjeros": g[["llegadas_no_residentes", "llegadas"]].apply(extranjeros),
    })


def conclusion(texto: str):
    st.info(texto, icon="💡")


def que_hacer(texto: str):
    st.success(texto, icon="✅")


def fig_base(fig, alto=360):
    fig.update_layout(height=alto, margin=dict(t=20, b=10, l=10, r=10), legend=dict(orientation="h", y=1.1))
    return fig


# ============================================================================= menú
PAGINAS = {
    "🏠 Inicio": "inicio",
    "🏨 ¿Cómo le fue a Manzanillo?": "anio",
    "📅 ¿Cuándo se llenan los hoteles?": "temporadas",
    "🌊 ¿Cómo vamos contra la competencia?": "competencia",
    "🗺️ ¿Dónde está la oferta de hospedaje?": "mapa",
    "🔍 ¿Qué tan confiables son los datos?": "confianza",
}
st.sidebar.markdown("## 🏨 Observatorio Hotelero\n**Colima · Manzanillo**")
pagina = PAGINAS[st.sidebar.radio("Elige una pregunta", list(PAGINAS))]
st.sidebar.divider()
st.sidebar.caption(f"Datos de ocupación hasta **{MESES_LARGO[int(oro[oro.anio == ANIO_MAX].mes.max()) - 1]} "
                   f"de {ANIO_MAX}**. Se actualizan solos cada semana.")
st.sidebar.caption("Fuentes oficiales: SECTUR-DataTur, Banco de México e INEGI. Elaboración propia.")


# ============================================================================= INICIO
if pagina == "inicio":
    mz = oro[oro.centro == "Manzanillo"]
    o_actual = ocupacion(mz[mz.anio == ANIO_MAX])
    meses_mz = por_mes(mz[NORMAL])
    peor = int(meses_mz.idxmin())
    pac = oro[(oro.litoral == "Pacífico") & (oro.periodo_covid == "Pospandemia")]
    rank = resumen_por(pac, "centro")["ocupacion"].sort_values(ascending=False)
    pos = list(rank.index).index("Manzanillo") + 1
    est = D["est"]
    pct_mz = 100 * (est.municipio_espacial == "Manzanillo").mean()

    st.title("Observatorio de Ocupación Hotelera de Colima")
    st.markdown(f"### De cada 10 cuartos de hotel en Manzanillo, se ocupan **{o_actual / 10:.1f}**.")
    st.markdown("Este tablero explica **cuándo** se llenan los hoteles, **contra quién compite** Manzanillo y "
                "**dónde** está la oferta de hospedaje, con datos oficiales que se actualizan solos. Está pensado "
                "para **hoteleros** y para la **Secretaría de Turismo**.")

    st.markdown("#### ¿Cómo se usa?")
    c = st.columns(3)
    pasos = [("1️⃣ Elige una pregunta", "En el menú de la izquierda. Cada sección contesta una duda concreta."),
             ("2️⃣ Lee el recuadro azul 💡", "Ahí está la respuesta en una frase. La gráfica es la evidencia."),
             ("3️⃣ Revisa el recuadro verde ✅", "Te sugiere qué decisión tomar con esa información.")]
    for col, (t, d) in zip(c, pasos):
        col.markdown(f"<div class='tarjeta'><h4>{t}</h4><p>{d}</p></div>", unsafe_allow_html=True)

    st.markdown("#### Las respuestas en corto")
    tarjetas = [
        ("🏨 ¿Cómo le fue a Manzanillo?", f"En {ANIO_MAX} se ocupó el **{o_actual:.0f} %** de los cuartos."),
        ("📅 ¿Cuándo se llenan?", f"Lo mejor: **{' y '.join(MESES_LARGO[m - 1] for m in sorted(meses_mz.nlargest(2).index))}**. "
                                 f"Lo peor: **{MESES_LARGO[peor - 1]}** ({meses_mz[peor]:.0f} %)."),
        ("🌊 ¿Contra la competencia?", f"Manzanillo es **{pos}.º de {len(rank)}** destinos de playa del Pacífico."),
        ("🗺️ ¿Dónde está la oferta?", f"Manzanillo tiene el **{pct_mz:.0f} %** de todo el hospedaje de Colima."),
    ]
    c = st.columns(4)
    for col, (t, d) in zip(c, tarjetas):
        with col:
            st.markdown(f"<div class='tarjeta'><h4>{t}</h4></div>", unsafe_allow_html=True)
            st.markdown(d)
    st.caption("La ocupación indica qué parte de los cuartos disponibles se vendió en el periodo.")


# ============================================================================= AÑO
elif pagina == "anio":
    st.title("🏨 ¿Cómo le fue a Manzanillo?")
    anio = st.select_slider("Año", options=sorted(int(x) for x in oro.anio.unique()), value=ANIO_MAX)
    mz = oro[oro.centro == "Manzanillo"]
    a, b = mz[mz.anio == anio], mz[mz.anio == anio - 1]
    hay_prev = not b.empty

    c = st.columns(4)
    c[0].metric("Cuartos ocupados", f"{ocupacion(a):.0f} de cada 100",
                f"{ocupacion(a) - ocupacion(b):+.1f} vs {anio - 1}" if hay_prev else None)
    c[1].metric("Turistas que llegaron", f"{a.llegadas.sum() / 1e6:.2f} millones",
                f"{100 * (a.llegadas.sum() / b.llegadas.sum() - 1):+.0f} % vs {anio - 1}" if hay_prev else None)
    c[2].metric("Noches que se queda cada turista", f"{estadia(a):.1f}",
                f"{estadia(a) - estadia(b):+.1f} vs {anio - 1}" if hay_prev else None)
    c[3].metric("Turistas extranjeros", f"{extranjeros(a):.0f} de cada 100")

    if hay_prev:
        dif = ocupacion(a) - ocupacion(b)
        tendencia = "mejor" if dif > 0.5 else "peor" if dif < -0.5 else "casi igual"
        conclusion(f"En {anio} a Manzanillo le fue **{tendencia}** que en {anio - 1}: se ocupó el "
                   f"**{ocupacion(a):.0f} %** de los cuartos ({dif:+.1f} puntos). Casi todos los turistas son "
                   f"mexicanos; los extranjeros son apenas {extranjeros(a):.0f} de cada 100.")

    st.subheader(f"Mes por mes: {anio} contra {anio - 1}" if hay_prev else f"Mes por mes: {anio}")
    m = pd.DataFrame({"mes": MESES, "actual": por_mes(a).reindex(range(1, 13)).values})
    fig = go.Figure()
    if hay_prev:
        fig.add_bar(x=m.mes, y=por_mes(b).reindex(range(1, 13)).values, name=str(anio - 1), marker_color="#c9d3de")
    fig.add_bar(x=m.mes, y=m.actual, name=str(anio), marker_color=AZUL, text=m.actual.round(0),
                textposition="outside")
    fig.update_yaxes(title="% de cuartos ocupados", range=[0, 100])
    st.plotly_chart(fig_base(fig), width="stretch")

    st.subheader("¿Va subiendo o bajando? (2016 a hoy)")
    anual = resumen_por(mz, "anio").reset_index()
    col1, col2 = st.columns(2)
    with col1:
        anual["grupo"] = anual.anio.eq(anio).map({True: "Año elegido", False: "Otros años"})
        fig = px.bar(anual, x="anio", y="ocupacion", text_auto=".0f", color="grupo",
                     color_discrete_map={"Año elegido": AZUL, "Otros años": "#c9d3de"},
                     labels={"ocupacion": "% de cuartos ocupados", "anio": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig_base(fig, 300), width="stretch")
        st.caption("2020 cae por la pandemia; desde 2023 Manzanillo supera sus niveles de antes.")
    with col2:
        fig = px.line(anual, x="anio", y="estadia", markers=True, labels={"estadia": "Noches por turista", "anio": ""})
        fig.update_traces(line=dict(color=NARANJA, width=3))
        fig.update_yaxes(range=[0, 3.2])
        st.plotly_chart(fig_base(fig, 300), width="stretch")
        st.caption(f"Cada turista se queda menos: {anual.estadia.iloc[0]:.1f} noches en {int(anual.anio.iloc[0])} "
                   f"contra {anual.estadia.iloc[-1]:.1f} en {int(anual.anio.iloc[-1])}.")
    que_hacer("Manzanillo se volvió un destino de **fin de semana**. Paquetes de 3 noches o promociones de "
              "domingo a jueves pueden alargar la estancia y llenar los días entre semana.")


# ============================================================================= TEMPORADAS
elif pagina == "temporadas":
    st.title("📅 ¿Cuándo se llenan los hoteles?")
    centros = sorted(oro.centro.unique())
    destino = st.selectbox("Destino", centros, index=centros.index("Manzanillo"))
    s = por_mes(oro[(oro.centro == destino) & NORMAL]).reindex(range(1, 13))
    mejor, peor = int(s.idxmax()), int(s.idxmin())
    df = pd.DataFrame({"mes": MESES, "ocupacion": s.values})
    df["nivel"] = df.ocupacion.map(lambda v: "Lleno" if v >= 60 else "Regular" if v >= 40 else "Flojo")

    conclusion(f"En **{destino}** el mejor mes es **{MESES_LARGO[mejor - 1]}** ({s[mejor]:.0f} % de cuartos ocupados) "
               f"y el peor es **{MESES_LARGO[peor - 1]}** ({s[peor]:.0f} %): en {MESES_LARGO[peor - 1]} se llenan "
               f"apenas {s[peor] / 10:.0f} de cada 10 cuartos.")
    fig = px.bar(df, x="mes", y="ocupacion", color="nivel", text_auto=".0f",
                 color_discrete_map={"Lleno": VERDE, "Regular": AMARILLO, "Flojo": ROJO},
                 category_orders={"nivel": ["Lleno", "Regular", "Flojo"], "mes": MESES},
                 labels={"ocupacion": "% de cuartos ocupados (promedio)", "mes": "", "nivel": ""})
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(fig_base(fig, 380), width="stretch")
    st.caption("🟢 Lleno: 60 % o más · 🟡 Regular: 40–60 % · 🔴 Flojo: menos de 40 %. "
               "Promedio de 2016 a 2024 sin los meses de pandemia.")

    flojos = [MESES_LARGO[i] for i in range(12) if s.iloc[i] < 40]
    if flojos:
        que_hacer(f"Meses flojos: **{', '.join(flojos)}**. Buen momento para promociones, convenios con empresas "
                  "y escuelas, mantenimiento y vacaciones del personal. En los meses llenos conviene subir tarifas "
                  "y contratar personal eventual con anticipación.")
    else:
        que_hacer("Este destino no tiene meses flojos (menos de 40 %). En los meses de mayor demanda conviene "
                  "subir tarifas y contratar personal eventual con anticipación.")

    with st.expander("Ver año por año (mapa de calor)"):
        piv = oro[oro.centro == destino].pivot_table(index="anio", columns="mes", values="ocupacion_pct")
        piv.columns = [MESES[c - 1] for c in piv.columns]
        fig = px.imshow(piv, text_auto=".0f", color_continuous_scale="Blues", aspect="auto",
                        labels=dict(color="% ocupado", x="", y=""))
        st.plotly_chart(fig_base(fig, 360), width="stretch")
        st.caption("Más oscuro = más lleno. La franja clara de 2020 es la pandemia.")


# ============================================================================= COMPETENCIA
elif pagina == "competencia":
    st.title("🌊 ¿Cómo vamos contra la competencia?")
    st.markdown("Comparamos a Manzanillo con los **destinos de playa del Pacífico mexicano**.")
    with st.expander("Cambiar periodo"):
        periodo = st.radio("Periodo", ["Después de la pandemia (2022-2024)", "Antes de la pandemia (2016-2019)"],
                           label_visibility="collapsed")
    filtro = "Pospandemia" if periodo.startswith("Después") else "Prepandemia"
    res = resumen_por(oro[(oro.litoral == "Pacífico") & (oro.periodo_covid == filtro)], "centro")
    res = res.sort_values("ocupacion").reset_index()
    res["color"] = res.centro.map(lambda c: "Manzanillo" if c == "Manzanillo" else "Otros")
    pos = len(res) - int(res.index[res.centro == "Manzanillo"][0])
    lider, mz = res.iloc[-1], res[res.centro == "Manzanillo"].iloc[0]

    conclusion(f"Manzanillo ocupa el lugar **{pos} de {len(res)}**. El líder, **{lider.centro}**, llena el "
               f"**{lider.ocupacion:.0f} %** de sus cuartos contra el **{mz.ocupacion:.0f} %** de Manzanillo: "
               f"una diferencia de **{lider.ocupacion - mz.ocupacion:.0f} puntos**.")
    fig = px.bar(res, y="centro", x="ocupacion", orientation="h", text_auto=".0f", color="color",
                 color_discrete_map={"Manzanillo": AZUL, "Otros": "#c9d3de"},
                 labels={"ocupacion": "% de cuartos ocupados", "centro": ""})
    fig.update_layout(showlegend=False)
    fig.update_yaxes(categoryorder="array", categoryarray=list(res.centro))   # el mejor arriba
    st.plotly_chart(fig_base(fig, 470), width="stretch")

    c1, c2 = st.columns(2)
    for col, var, titulo, eje, fmt, colores in [
        (c1, "estadia", "¿Cuántas noches se quedan?", "Noches por turista", ".1f", (NARANJA, "#e6d3c3")),
        (c2, "extranjeros", "¿Cuántos turistas son extranjeros?", "% de turistas extranjeros", ".0f",
         (VERDE, "#cfe3d5"))]:
        with col:
            st.subheader(titulo)
            orden = res.sort_values(var)
            fig = px.bar(orden, y="centro", x=var, orientation="h", text_auto=fmt, color="color",
                         color_discrete_map={"Manzanillo": colores[0], "Otros": colores[1]},
                         labels={var: eje, "centro": ""})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(categoryorder="array", categoryarray=list(orden.centro))
            st.plotly_chart(fig_base(fig, 420), width="stretch")
    que_hacer(f"Los destinos líderes atraen turismo **extranjero** y estancias **largas**. Manzanillo depende casi "
              f"por completo del turismo nacional de fin de semana ({mz.extranjeros:.0f} % extranjeros, "
              f"{mz.estadia:.1f} noches). Más vuelos y promoción en el extranjero son la palanca principal para "
              "acercarse a los líderes.")


# ============================================================================= MAPA
elif pagina == "mapa":
    st.title("🗺️ ¿Dónde está la oferta de hospedaje?")
    mun, est = D["mun"], D["est"]
    mz = mun[mun.nomgeo == "Manzanillo"].iloc[0]
    renta = est.tipo_alojamiento.isin(["Departamento o casa amueblada", "Cabañas y villas"]).sum()
    c = st.columns(4)
    c[0].metric("Lugares para hospedarse en Colima", f"{len(est)}")
    c[1].metric("Están en Manzanillo", f"{mz.establecimientos:.0f} ({mz.pct_oferta_estatal:.0f} %)")
    c[2].metric("Son negocios pequeños", f"{100 * (est.tamano == 'Micro').mean():.0f} %",
                help="Menos de 10 trabajadores")
    c[3].metric("Departamentos, casas y cabañas", f"{renta}",
                help="Oferta tipo renta vacacional que no aparece en las estadísticas de hoteles")
    top_hab = mun.sort_values("establecimientos_por_10k_hab").iloc[-1].nomgeo
    conclusion(f"Casi la mitad del hospedaje del estado está en **Manzanillo**. **{top_hab}** tiene más lugares por "
               "habitante por sus playas, y Villa de Álvarez casi no tiene: sus visitantes duermen en Colima capital.")

    with st.expander("Filtrar por tipo de lugar"):
        tipos = st.multiselect("Tipo", list(COLOR_TIPO), default=list(COLOR_TIPO), label_visibility="collapsed")
    fig = px.choropleth_map(mun, geojson=geo_municipios(), locations="cvegeo", featureidkey="properties.cvegeo",
                            color="establecimientos", color_continuous_scale="Greys", opacity=.45,
                            hover_name="nomgeo", hover_data={"cvegeo": False, "establecimientos": True},
                            labels={"establecimientos": "Lugares"},
                            map_style="carto-positron", center={"lat": 19.08, "lon": -104.05}, zoom=8.3)
    e = est[est.tipo_alojamiento.isin(tipos)]
    tam = e.tamano.map({"Micro": 7, "Pequeño": 11, "Mediano": 16, "Grande": 22})
    for tipo, sub in e.groupby("tipo_alojamiento"):
        fig.add_trace(go.Scattermap(lat=sub.latitud, lon=sub.longitud, mode="markers", name=tipo,
                                    marker=dict(size=tam.loc[sub.index], opacity=.9, color=COLOR_TIPO[tipo]),
                                    text=sub.tipo_alojamiento + " · " + sub.per_ocu + " · " + sub.municipio_espacial,
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False,
                      legend=dict(orientation="h", y=-0.02))
    st.plotly_chart(fig, width="stretch")
    st.caption("Cada punto es un lugar de hospedaje; el tamaño indica cuántas personas trabajan ahí. "
               "Pasa el mouse para ver el detalle. Fuente: INEGI, DENUE 2026; elaboración propia.")
    que_hacer("Hay departamentos, casas y cabañas que compiten con los hoteles pero no aparecen en las estadísticas "
              "oficiales de ocupación. Conviene considerarlos al fijar precios, sobre todo en temporada alta.")


# ============================================================================= CONFIANZA
else:
    st.title("🔍 ¿Qué tan confiables son los datos?")
    cal, lin, fal = D["calidad"], D["linaje"], D["faltantes"]
    total = sum(p["registros_entrada"] for p in cal["puertas"] if p["etapa"].endswith("entrada"))
    c = st.columns(3)
    c[0].metric("Registros revisados automáticamente", f"{total:,}")
    c[1].metric("Separados por tener errores", f"{cal['cuarentena_total']}",
                help="No se borran: quedan guardados con su motivo")
    c[2].metric("Datos que se pueden rastrear a su origen",
                f"{100 * (lin['ids_oro'] - lin['registros_oro_sin_linaje']) / lin['ids_oro']:.0f} %")
    conclusion(f"Todos los datos vienen de **fuentes oficiales** (SECTUR, Banco de México e INEGI). Antes de mostrarse, "
               f"un sistema revisa automáticamente {total:,} registros y aparta los que tienen errores, por ejemplo "
               f"más cuartos ocupados que cuartos en el hotel. Sólo {cal['cuarentena_total']} tuvieron problemas.")

    st.subheader("¿De dónde salen los datos?")
    st.dataframe(pd.DataFrame([
        ["🏨 Ocupación de hoteles", "Secretaría de Turismo (DataTur)", "Mensual"],
        ["💵 Tipo de cambio e inflación", "Banco de México", "Diaria / mensual"],
        ["🗺️ Lugares de hospedaje y mapas", "INEGI (DENUE y Marco Geoestadístico)", "Anual"],
    ], columns=["Dato", "Fuente oficial", "Frecuencia"]), hide_index=True, width="stretch")
    st.markdown(f"- Los datos se descargan y revisan **solos cada semana**.\n"
                f"- Cuando faltaban meses aislados se estimaron con los meses vecinos ({fal['huecos_imputados']} casos); "
                "cuando una categoría de hotel no existía, **no se inventó**.\n"
                "- La pandemia y el huracán Otis se conservan tal cual: son hechos reales, no errores.")

    with st.expander("Ver los registros con errores"):
        q = D["cuarentena"]
        st.dataframe(q[[x for x in ["periodo", "anio", "mes", "centro", "categoria", "motivo"] if x in q]],
                     hide_index=True, width="stretch")
    with st.expander("Para auditores: rastrear un dato hasta su archivo original"):
        st.markdown("Escribe el destino y el mes (por ejemplo `Manzanillo|2024-07`) y verás de qué filas exactas "
                    "de los archivos oficiales salió ese dato y cuándo se descargaron.")
        c1, c2 = st.columns([2, 3])
        ej = c1.selectbox("Ejemplos", ["Manzanillo|2024-07", "Colima|2020-04", "municipio|06007"])
        id_oro = c2.text_input("Dato a rastrear", ej, key=f"id_oro_{ej}")
        if id_oro:
            r = linaje.rastrear(id_oro.strip(), tabla_linaje(), limite=5)
            if r.empty:
                st.warning("No encontré ese dato. Revisa que el formato sea Destino|AAAA-MM.")
            else:
                st.dataframe(r[["fuente", "rol", "archivo_origen", "fila_origen", "fecha_ingesta"]]
                             .rename(columns={"fuente": "Fuente", "rol": "Qué se hizo", "archivo_origen": "Archivo",
                                              "fila_origen": "Fila", "fecha_ingesta": "Descargado"}),
                             hide_index=True, width="stretch")
    with st.expander("Historial de descargas"):
        b = D["bitacora"].sort_values("fecha_utc", ascending=False)
        st.dataframe(b[["fecha_utc", "fuente", "estado"]].head(20), hide_index=True, width="stretch")
        st.caption("'bloqueado' = el servidor de SECTUR no permite descargas automáticas desde fuera de México; "
                   "el sistema lo respeta y usa la última versión descargada.")
