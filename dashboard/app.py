"""Observatorio Hotelero de Colima — tablero para el cliente.

Diseñado para hoteleros y para la Secretaría de Turismo: cinco pestañas, cada una responde una
pregunta de negocio con la conclusión escrita y una recomendación accionable.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python -m streamlit run dashboard/app.py
"""
from __future__ import annotations

import calendar
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

# ----------------------------------------------------------------------------- identidad visual
TINTA, TEAL, TEAL_CLARO, CORAL, ARENA, GRIS, VERDE = (
    "#1B2A3A", "#0E7C86", "#BFE3E6", "#E4572E", "#F2C14E", "#C5CED8", "#2E9E6B")
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_L = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"]
COLOR_TIPO = {"Hotel": TEAL, "Motel": CORAL, "Departamento o casa amueblada": "#7A5CC7",
              "Cabañas y villas": VERDE, "Pensión o casa de huéspedes": ARENA, "Campamento o albergue": "#5B8DEF"}
TEMPORADA = {
    "Alta": {"color": TEAL, "fondo": "#E3F4F5", "icono": "🔥",
             "accion": "Sube tarifas, contrata personal eventual con 4 a 6 semanas de anticipación y asegura inventario."},
    "Media": {"color": "#C99A1E", "fondo": "#FBF3DC", "icono": "⚖️",
              "accion": "Mantén la tarifa base y lanza promociones para fines de semana largos y puentes."},
    "Baja": {"color": CORAL, "fondo": "#FCE7E1", "icono": "🧊",
             "accion": "Promociones, convenios con empresas y escuelas, mantenimiento y vacaciones del personal."},
}

st.set_page_config(page_title="Observatorio Hotelero · Colima", page_icon="🏨", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stText {{ font-family: 'Inter', sans-serif; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1280px; }}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ color: {TINTA}; letter-spacing: -0.02em; }}

.hero {{ background: linear-gradient(120deg, #0B3C5D 0%, {TEAL} 100%); color: white; border-radius: 18px;
        padding: 26px 32px; margin-bottom: 14px; box-shadow: 0 10px 30px rgba(14,124,134,.25); }}
.hero h1 {{ color: white; font-size: 1.9rem; margin: 0 0 4px 0; font-weight: 800; }}
.hero p {{ margin: 0; opacity: .9; font-size: 1.02rem; }}
.hero .chip {{ display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.3);
              border-radius: 999px; padding: 3px 12px; font-size: .8rem; margin: 12px 8px 0 0; }}

.kpi {{ background: white; border-radius: 16px; padding: 18px 20px; border: 1px solid #E6EBF1;
       box-shadow: 0 2px 10px rgba(27,42,58,.05); height: 100%; }}
.kpi .icono {{ font-size: 1.5rem; }}
.kpi .valor {{ font-size: 2.1rem; font-weight: 800; color: {TINTA}; line-height: 1.1; margin-top: 6px; }}
.kpi .etiqueta {{ font-size: .86rem; color: #5B6B7C; margin-top: 2px; }}
.kpi .delta {{ font-size: .8rem; font-weight: 600; margin-top: 8px; display: inline-block; padding: 2px 9px;
              border-radius: 999px; }}
.delta.up {{ background: #E3F5EC; color: {VERDE}; }} .delta.down {{ background: #FCE7E1; color: {CORAL}; }}
.delta.neutral {{ background: #EEF1F5; color: #5B6B7C; }}

.insight {{ border-radius: 16px; padding: 18px 20px; height: 100%; border: 1px solid transparent; }}
.insight h4 {{ margin: 0 0 6px 0; font-size: 1rem; }}
.insight p {{ margin: 0; font-size: .93rem; color: #33475B; line-height: 1.45; }}
.insight.bueno {{ background: #E9F7F0; border-color: #C9EBD9; }} .insight.bueno h4 {{ color: {VERDE}; }}
.insight.alerta {{ background: #FDEEE9; border-color: #F7D3C7; }} .insight.alerta h4 {{ color: {CORAL}; }}
.insight.oportunidad {{ background: #E6F3F5; border-color: #C3E3E7; }} .insight.oportunidad h4 {{ color: {TEAL}; }}

.mes {{ border-radius: 14px; padding: 12px 10px; text-align: center; border: 2px solid transparent; }}
.mes .nombre {{ font-weight: 700; font-size: .95rem; color: {TINTA}; }}
.mes .pct {{ font-weight: 800; font-size: 1.45rem; margin: 2px 0; }}
.mes .tag {{ font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}

.seccion {{ font-size: .78rem; font-weight: 700; color: {TEAL}; text-transform: uppercase; letter-spacing: .08em;
           margin: 6px 0 2px 0; }}
.subtitulo {{ color: #5B6B7C; margin-top: -6px; margin-bottom: 14px; }}
.recomendacion {{ background: white; border-left: 5px solid {TEAL}; border-radius: 10px; padding: 14px 18px;
                 box-shadow: 0 2px 10px rgba(27,42,58,.05); margin: 8px 0 4px 0; }}
.recomendacion b {{ color: {TEAL}; }}
.pie {{ color: #7A8796; font-size: .78rem; margin-top: 26px; border-top: 1px solid #E6EBF1; padding-top: 12px; }}

[data-testid="stTabs"] [role="tablist"] {{ gap: 8px; border-bottom: 2px solid #E6EBF1; padding-bottom: 0; }}
[data-testid="stTab"] {{ background: white; border-radius: 12px 12px 0 0; padding: 10px 18px !important;
                        border: 1px solid #E6EBF1; border-bottom: none; height: auto !important; }}
[data-testid="stTab"] p {{ font-size: 1rem !important; font-weight: 600; color: #42566B; }}
[data-testid="stTab"]:hover p {{ color: {TEAL}; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {TEAL}; border-color: {TEAL}; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: white !important; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"]
    {{ display: none; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- datos
@st.cache_data
def cargar():
    o = pd.read_csv(ORO / "destino_mes.csv", low_memory=False)
    o["fecha"] = pd.to_datetime(o["periodo"])
    return {
        "oro": o,
        "mun": pd.read_csv(ORO / "municipio_hospedaje.csv", dtype={"cvegeo": str}),
        "est": pd.read_csv(ORO / "establecimientos_hospedaje.csv"),
        "calidad": json.loads((REP / "E1" / "calidad.json").read_text(encoding="utf-8")),
        "faltantes": json.loads((REP / "E1" / "faltantes.json").read_text(encoding="utf-8")),
        "linaje": json.loads((REP / "E2" / "linaje.json").read_text(encoding="utf-8")),
        "geo": json.loads((REP / "E2" / "geoespacial.json").read_text(encoding="utf-8")),
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
ANIO_MAX = int(oro.anio.max())
MES_MAX = int(oro[oro.anio == ANIO_MAX].mes.max())


def ocupacion(d):
    return 100 * d["cuartos_ocupados"].sum() / d["cuartos_disponibles"].sum()


def estadia(d):
    return d["turistas_noche"].sum() / d["llegadas"].sum()


def extranjeros(d):
    return 100 * d["llegadas_no_residentes"].sum() / d["llegadas"].sum()


def resumen(d, por):
    g = d.groupby(por)
    return pd.DataFrame({
        "ocupacion": g[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocupacion),
        "estadia": g[["turistas_noche", "llegadas"]].apply(estadia),
        "extranjeros": g[["llegadas_no_residentes", "llegadas"]].apply(extranjeros),
    })


def plan_mensual(d):
    """Plan de 12 meses con datos pospandemia (2022 en adelante): ocupación típica, cuartos vacíos por
    noche y temporada RELATIVA al propio destino (sus 4 meses más fuertes, intermedios y más débiles)."""
    p = d[d.periodo_covid == "Pospandemia"]
    g = p.groupby("mes").agg(disp=("cuartos_disponibles", "sum"), ocup=("cuartos_ocupados", "sum"),
                             anios=("anio", "nunique"))
    g["ocupacion"] = 100 * g.ocup / g.disp
    dias = pd.Series({m: calendar.monthrange(2023, m)[1] for m in range(1, 13)})
    g["vacios_noche"] = (g.disp - g.ocup) / g.anios / dias.reindex(g.index)
    rango = g["ocupacion"].rank(method="first")
    g["temporada"] = pd.cut(rango, [0, 4, 8, 12], labels=["Baja", "Media", "Alta"]).astype(str)
    return g.reindex(range(1, 13))


def kpi(col, icono, valor, etiqueta, delta=None, sentido="neutral"):
    d = f"<div class='delta {sentido}'>{delta}</div>" if delta else ""
    col.markdown(f"<div class='kpi'><div class='icono'>{icono}</div><div class='valor'>{valor}</div>"
                 f"<div class='etiqueta'>{etiqueta}</div>{d}</div>", unsafe_allow_html=True)


def insight(col, clase, titulo, texto):
    col.markdown(f"<div class='insight {clase}'><h4>{titulo}</h4><p>{texto}</p></div>", unsafe_allow_html=True)


def recomendacion(texto):
    st.markdown(f"<div class='recomendacion'>✅ <b>Recomendación:</b> {texto}</div>", unsafe_allow_html=True)


def encabezado(seccion, titulo, subtitulo):
    st.markdown(f"<div class='seccion'>{seccion}</div>", unsafe_allow_html=True)
    st.markdown(f"### {titulo}")
    st.markdown(f"<div class='subtitulo'>{subtitulo}</div>", unsafe_allow_html=True)


def estilo(fig, alto=380, leyenda=True):
    fig.update_layout(height=alto, margin=dict(t=30, b=10, l=10, r=10), plot_bgcolor="white",
                      paper_bgcolor="white", font=dict(family="Inter, sans-serif", color=TINTA, size=13),
                      legend=dict(orientation="h", y=1.12, x=0, title=None) if leyenda else None,
                      showlegend=leyenda, hoverlabel=dict(font_family="Inter, sans-serif"))
    fig.update_xaxes(showgrid=False, linecolor="#D9E0E8")
    fig.update_yaxes(gridcolor="#EEF1F5", zeroline=False)
    return fig


def signo(v, unidad="", invertir=False):
    if abs(v) < 0.05:
        return f"igual que el año anterior", "neutral"
    bueno = (v > 0) != invertir
    return f"{'▲' if v > 0 else '▼'} {abs(v):.1f}{unidad} vs año anterior", ("up" if bueno else "down")


# ----------------------------------------------------------------------------- encabezado
destinos = sorted(oro.centro.unique())
c_hero, c_sel = st.columns([4, 1.25], vertical_alignment="center")
with c_sel:
    destino = st.selectbox("📍 Destino a analizar", destinos, index=destinos.index("Manzanillo"),
                           help="Todo el tablero se ajusta al destino que elijas.")
d_dest = oro[oro.centro == destino]
with c_hero:
    st.markdown(f"""<div class='hero'><h1>Observatorio Hotelero · {destino}</h1>
        <p>Cuándo se llenan los hoteles, contra quién competimos y qué hacer cada mes.</p>
        <span class='chip'>📅 Datos hasta {MESES_L[MES_MAX - 1]} {ANIO_MAX}</span>
        <span class='chip'>🔄 Actualización automática semanal</span>
        <span class='chip'>🏛️ SECTUR · Banxico · INEGI</span></div>""", unsafe_allow_html=True)

with st.expander("👋 ¿Primera vez aquí? Así se usa este tablero (30 segundos)", expanded=False):
    c = st.columns(3)
    c[0].markdown("**1. Elige tu destino** arriba a la derecha (por defecto, Manzanillo).")
    c[1].markdown("**2. Recorre las pestañas** de izquierda a derecha: van de lo general a lo específico.")
    c[2].markdown("**3. Lee los recuadros de color y la recomendación ✅**: ahí está la respuesta; "
                  "las gráficas son la evidencia. Pasa el mouse sobre cualquier gráfica para ver el detalle.")

tab_res, tab_plan, tab_comp, tab_mapa, tab_conf = st.tabs(
    ["📊 Resumen", "🗓️ Planeador de temporadas", "🌊 Competencia", "🗺️ Mapa de hospedaje", "🛡️ Confiabilidad"])


# ============================================================================= RESUMEN
with tab_res:
    ANIO_D = int(d_dest.anio.max())   # último año con datos del destino (p. ej. El Fuerte llega a 2023)
    a = d_dest[d_dest.anio == ANIO_D]
    b = d_dest[d_dest.anio == ANIO_D - 1]
    pre = d_dest[d_dest.periodo_covid == "Prepandemia"]
    encabezado("Resumen ejecutivo", f"¿Cómo le fue a {destino} en {ANIO_D}?",
               "Los cuatro números que hay que saber, comparados con el año anterior.")
    c = st.columns(4)
    v, s = signo(ocupacion(a) - ocupacion(b), " pts")
    kpi(c[0], "🏨", f"{ocupacion(a):.0f}%", "de los cuartos se ocuparon", v, s)
    v, s = signo(100 * (a.llegadas.sum() / b.llegadas.sum() - 1), "%")
    kpi(c[1], "🧳", f"{a.llegadas.sum() / 1e6:.2f} M" if a.llegadas.sum() > 1e6 else f"{a.llegadas.sum() / 1e3:.0f} mil",
        "turistas llegaron", v, s)
    v, s = signo(estadia(a) - estadia(b), " noches")
    kpi(c[2], "🌙", f"{estadia(a):.1f}", "noches se queda cada turista", v, s)
    v, s = signo(extranjeros(a) - extranjeros(b), " pts")
    kpi(c[3], "✈️", f"{extranjeros(a):.0f}%", "de los turistas son extranjeros", v, s)

    st.write("")
    plan = plan_mensual(d_dest)
    pac = oro[(oro.litoral == d_dest.litoral.iloc[0]) & (oro.periodo_covid == "Pospandemia")] \
        if d_dest.tipo_centro.iloc[0] == "Centros de Playa" else \
        oro[(oro.tipo_centro == "Ciudades") & (oro.periodo_covid == "Pospandemia")]
    rk = resumen(pac, "centro").sort_values("ocupacion", ascending=False)
    lider = rk.index[0] if rk.index[0] != destino else rk.index[1]
    peor = int(plan.ocupacion.idxmin())
    c = st.columns(3)
    rec = ocupacion(a) - ocupacion(pre)
    insight(c[0], "bueno", "👍 Lo bueno",
            f"{destino} {'ya supera' if rec > 0 else 'aún no recupera'} su nivel de antes de la pandemia: "
            f"<b>{ocupacion(a):.0f}%</b> de ocupación en {ANIO_D} contra <b>{ocupacion(pre):.0f}%</b> en 2016-2019.")
    est_pre, est_hoy = estadia(pre), estadia(a)
    insight(c[1], "alerta", "⚠️ Lo preocupante",
            f"Cada turista se queda <b>{est_hoy:.1f} noches</b> (antes {est_pre:.1f}) y sólo "
            f"<b>{extranjeros(a):.0f} de cada 100</b> son extranjeros: dependencia del turismo nacional de fin de semana."
            if est_hoy < est_pre else
            f"Sólo <b>{extranjeros(a):.0f} de cada 100</b> turistas son extranjeros: alta dependencia del turismo nacional.")
    insight(c[2], "oportunidad", "💡 La oportunidad",
            f"El mes más flojo es <b>{MESES_L[peor - 1]}</b>: cada noche quedan unos "
            f"<b>{plan.vacios_noche[peor]:,.0f} cuartos vacíos</b>. {lider} llena "
            f"<b>{rk.ocupacion[lider] - rk.ocupacion.get(destino, 0):.0f} puntos más</b> que {destino}.")

    st.write("")
    encabezado("Tendencia", "¿Vamos mejorando?", "Ocupación anual del destino frente al líder de su grupo y al promedio.")
    anual = resumen(d_dest, "anio").reset_index()
    lid = resumen(oro[oro.centro == lider], "anio").reset_index()
    grupo = resumen(oro[oro.centro.isin(pac.centro.unique())], "anio").reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=grupo.anio, y=grupo.ocupacion, name="Promedio del grupo", mode="lines",
                             line=dict(color=GRIS, width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=lid.anio, y=lid.ocupacion, name=f"{lider} (líder)", mode="lines+markers",
                             line=dict(color=ARENA, width=2.5)))
    fig.add_trace(go.Scatter(x=anual.anio, y=anual.ocupacion, name=destino, mode="lines+markers+text",
                             line=dict(color=TEAL, width=4), marker=dict(size=9),
                             text=[f"{v:.0f}%" for v in anual.ocupacion], textposition="top center"))
    fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor="#EEF1F5", opacity=1, line_width=0, layer="below",
                  annotation_text="Pandemia", annotation_position="top left")
    fig.update_yaxes(title="% de cuartos ocupados", ticksuffix="%", range=[0, 100])
    fig.update_xaxes(dtick=1)
    st.plotly_chart(estilo(fig, 400), width="stretch", config={"displayModeBar": False})


# ============================================================================= PLANEADOR
with tab_plan:
    encabezado("Planeador de temporadas", f"¿Qué hago cada mes en {destino}?",
               "Ocupación típica de cada mes después de la pandemia (2022 en adelante) y la acción recomendada. "
               "La temporada se calcula para tu destino: sus 4 meses más fuertes, los intermedios y los 4 más débiles.")
    plan = plan_mensual(d_dest)
    for fila in (range(1, 7), range(7, 13)):
        cols = st.columns(6)
        for col, m in zip(cols, fila):
            t = TEMPORADA[plan.temporada[m]]
            col.markdown(f"<div class='mes' style='background:{t['fondo']};border-color:{t['color']}33'>"
                         f"<div class='nombre'>{MESES[m - 1]}</div>"
                         f"<div class='pct' style='color:{t['color']}'>{plan.ocupacion[m]:.0f}%</div>"
                         f"<div class='tag' style='color:{t['color']}'>{t['icono']} {plan.temporada[m]}</div></div>",
                         unsafe_allow_html=True)
        st.write("")

    c1, c2 = st.columns([1, 1.6])
    with c1:
        sel = st.selectbox("Elige un mes para ver el plan", list(range(1, 13)),
                           format_func=lambda m: MESES_L[m - 1].capitalize(), index=8)
        t = TEMPORADA[plan.temporada[sel]]
        anterior = plan.ocupacion[sel - 1] if sel > 1 else plan.ocupacion[12]
        st.markdown(f"""<div class='insight' style='background:{t['fondo']};border-color:{t['color']}55'>
            <h4 style='color:{t['color']}'>{t['icono']} {MESES_L[sel - 1].capitalize()}: temporada {plan.temporada[sel].lower()}</h4>
            <p>Se ocupa en promedio el <b>{plan.ocupacion[sel]:.0f}%</b> de los cuartos
            ({plan.ocupacion[sel] - anterior:+.0f} puntos frente al mes anterior).<br>
            Cada noche quedan unos <b>{plan.vacios_noche[sel]:,.0f} cuartos vacíos</b> en el destino.</p></div>""",
                    unsafe_allow_html=True)
        recomendacion(t["accion"])
    with c2:
        df = plan.reset_index()
        df["mes_n"] = [MESES[m - 1] for m in df.mes]
        df["color"] = [TEMPORADA[x]["color"] for x in df.temporada]
        fig = go.Figure(go.Bar(x=df.mes_n, y=df.ocupacion, marker_color=df.color,
                               marker_line_width=[3 if m == sel else 0 for m in df.mes], marker_line_color=TINTA,
                               text=[f"{v:.0f}%" for v in df.ocupacion], textposition="outside",
                               customdata=df.vacios_noche,
                               hovertemplate="%{x}: %{y:.1f}% ocupado<br>%{customdata:,.0f} cuartos vacíos por noche"
                                             "<extra></extra>"))
        fig.update_yaxes(title="% de cuartos ocupados", ticksuffix="%",
                         range=[0, max(100, df.ocupacion.max() + 10)])
        st.plotly_chart(estilo(fig, 360, leyenda=False), width="stretch", config={"displayModeBar": False})

    descarga = plan.reset_index()[["mes", "ocupacion", "vacios_noche", "temporada"]].assign(
        mes=lambda x: [MESES_L[m - 1] for m in x.mes],
        accion=lambda x: [TEMPORADA[t]["accion"] for t in x.temporada]).round(1)
    descarga.columns = ["mes", "ocupacion_pct", "cuartos_vacios_por_noche", "temporada", "accion_recomendada"]
    st.download_button("⬇️ Descargar el plan anual (Excel/CSV)", descarga.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"plan_temporadas_{destino.lower().replace(' ', '_')}.csv", mime="text/csv")


# ============================================================================= COMPETENCIA
with tab_comp:
    es_playa = d_dest.tipo_centro.iloc[0] == "Centros de Playa"
    grupo_txt = f"destinos de playa del {d_dest.litoral.iloc[0]}" if es_playa else "ciudades monitoreadas"
    encabezado("Competencia", f"¿Cómo va {destino} contra los {grupo_txt}?",
               "Comparación después de la pandemia (2022 en adelante).")
    base = oro[(oro.litoral == d_dest.litoral.iloc[0]) if es_playa else (oro.tipo_centro == "Ciudades")]
    res = resumen(base[base.periodo_covid == "Pospandemia"], "centro").sort_values("ocupacion")
    pos = len(res) - list(res.index).index(destino)
    lider = res.index[-1]
    yo = res.loc[destino]
    c = st.columns(3)
    kpi(c[0], "🏆", f"{pos}.º de {len(res)}", "lugar en ocupación")
    kpi(c[1], "📏", f"{res.ocupacion[lider] - yo.ocupacion:.0f} pts" if lider != destino else "Líder",
        f"de distancia con {lider}" if lider != destino else "del grupo")
    kpi(c[2], "🌙", f"{yo.estadia:.1f} vs {res.estadia.max():.1f}", "noches por turista (tú vs el máximo)")
    st.write("")

    colores = [TEAL if i == destino else GRIS for i in res.index]
    fig = go.Figure(go.Bar(y=res.index, x=res.ocupacion, orientation="h", marker_color=colores,
                           text=[f"{v:.0f}%" for v in res.ocupacion], textposition="outside",
                           hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.update_xaxes(title="% de cuartos ocupados", ticksuffix="%", range=[0, res.ocupacion.max() + 12])
    fig.update_layout(title=dict(text="Ocupación promedio", font=dict(size=15)))
    st.plotly_chart(estilo(fig, 30 * len(res) + 90, leyenda=False), width="stretch", config={"displayModeBar": False})

    c1, c2 = st.columns(2)
    for col, var, titulo, fmt, sufijo in [(c1, "estadia", "Noches que se queda cada turista", ".1f", ""),
                                          (c2, "extranjeros", "% de turistas extranjeros", ".0f", "%")]:
        r = res.sort_values(var)
        fig = go.Figure(go.Bar(y=r.index, x=r[var], orientation="h",
                               marker_color=[CORAL if i == destino else GRIS for i in r.index],
                               text=[f"{v:{fmt}}{sufijo}" for v in r[var]], textposition="outside",
                               hovertemplate="%{y}: %{x:" + fmt + "}" + sufijo + "<extra></extra>"))
        fig.update_layout(title=dict(text=titulo, font=dict(size=15)))
        fig.update_xaxes(range=[0, r[var].max() * 1.18])
        col.plotly_chart(estilo(fig, 26 * len(r) + 90, leyenda=False), width="stretch",
                         config={"displayModeBar": False})
    lideres = res.sort_values("ocupacion").tail(3)
    recomendacion(f"Los tres destinos con más ocupación ({', '.join(lideres.index[::-1])}) reciben en promedio "
                  f"<b>{lideres.extranjeros.mean():.0f}% de turistas extranjeros</b> y retienen "
                  f"<b>{lideres.estadia.mean():.1f} noches</b>; {destino} tiene {yo.extranjeros:.0f}% y {yo.estadia:.1f}. "
                  "Atraer turismo internacional y paquetes de estancia larga es la palanca para acercarse a ellos.")


# ============================================================================= MAPA
with tab_mapa:
    mun, est = D["mun"], D["est"]
    mz = mun.sort_values("establecimientos").iloc[-1]
    encabezado("Oferta de hospedaje", "¿Dónde está la competencia en Colima?",
               f"Los {len(est)} lugares de hospedaje registrados en el DENUE del INEGI ({D['geo'].get('edicion_denue', '')}). "
               "Incluye departamentos y cabañas que no aparecen en las estadísticas de ocupación.")
    c = st.columns(4)
    kpi(c[0], "🏨", f"{len(est)}", "lugares para hospedarse en el estado")
    kpi(c[1], "📍", f"{mz.pct_oferta_estatal:.0f}%", f"están en {mz.nomgeo}")
    kpi(c[2], "🏠", f"{est.tipo_alojamiento.isin(['Departamento o casa amueblada', 'Cabañas y villas']).sum()}",
        "departamentos, casas y cabañas")
    kpi(c[3], "👥", f"{100 * (est.tamano == 'Micro').mean():.0f}%", "son negocios de menos de 10 personas")
    st.write("")
    tipos = st.multiselect("Mostrar en el mapa", list(COLOR_TIPO), default=list(COLOR_TIPO))
    fig = px.choropleth_map(mun, geojson=geo_municipios(), locations="cvegeo", featureidkey="properties.cvegeo",
                            color="establecimientos", color_continuous_scale=["#F5F7FA", "#9FB3C8"], opacity=.55,
                            hover_name="nomgeo", hover_data={"cvegeo": False, "establecimientos": True},
                            labels={"establecimientos": "Lugares"},
                            map_style="carto-positron", center={"lat": 19.05, "lon": -104.0}, zoom=8.75)
    e = est[est.tipo_alojamiento.isin(tipos)]
    for tipo, sub in e.groupby("tipo_alojamiento"):
        fig.add_trace(go.Scattermap(lat=sub.latitud, lon=sub.longitud, mode="markers", name=tipo,
                                    marker=dict(size=sub.tamano.map({"Micro": 8, "Pequeño": 12, "Mediano": 17,
                                                                     "Grande": 23}).to_numpy(),
                                                color=COLOR_TIPO[tipo], opacity=.9),
                                    text=sub.tipo_alojamiento + " · " + sub.per_ocu + " · " + sub.municipio_espacial,
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=580, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False,
                      legend=dict(orientation="h", y=-0.03, font=dict(family="Inter, sans-serif")))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": True})
    st.caption("El tamaño del punto indica cuántas personas trabajan ahí. Usa la rueda del mouse para acercar. "
               "Fuente: INEGI, DENUE; elaboración propia.")
    recomendacion("La renta vacacional (departamentos, casas y cabañas) compite con los hoteles pero no aparece en las "
                  "cifras oficiales de ocupación. Considérala al fijar precios, sobre todo en temporada alta.")


# ============================================================================= CONFIABILIDAD
with tab_conf:
    cal, lin, fal = D["calidad"], D["linaje"], D["faltantes"]
    total = sum(p["registros_entrada"] for p in cal["puertas"] if "entrada" in p["etapa"])
    encabezado("Confiabilidad", "¿Puedo confiar en estos números?",
               "Sí: los datos son oficiales y un sistema automático los revisa antes de mostrarlos.")
    c = st.columns(4)
    kpi(c[0], "🏛️", "3", "fuentes oficiales: SECTUR, Banxico e INEGI")
    kpi(c[1], "🔍", f"{total:,}", "registros revisados automáticamente")
    kpi(c[2], "🚫", f"{cal['cuarentena_total']}", "registros con errores apartados (no se usan)")
    kpi(c[3], "🔗", f"{100 * (lin['ids_oro'] - lin['registros_oro_sin_linaje']) / lin['ids_oro']:.0f}%",
        "de los datos se pueden rastrear a su archivo original")
    st.write("")
    c = st.columns(3)
    insight(c[0], "oportunidad", "🔄 Se actualiza solo",
            "Cada semana el sistema descarga los datos nuevos de las fuentes oficiales, los limpia, los revisa y "
            "actualiza este tablero. No hay captura manual.")
    insight(c[1], "bueno", "✅ Revisado antes de mostrar",
            "Se apartan registros imposibles, por ejemplo hoteles con más cuartos ocupados que cuartos totales. "
            f"Los meses aislados que faltaban se estimaron con sus vecinos ({fal['huecos_imputados']} casos) y no se "
            "inventaron datos donde una categoría de hotel no existía.")
    insight(c[2], "alerta", "📌 Qué tener en cuenta",
            "Las cifras de ocupación cubren hoteles registrados ante la Secretaría de Turismo. No incluyen renta "
            "vacacional tipo Airbnb. La pandemia y el huracán Otis se conservan tal cual: son hechos reales.")
    with st.expander("🔎 Para auditores: rastrear un dato hasta su archivo original"):
        st.markdown("Escribe el destino y el mes, por ejemplo `Manzanillo|2024-07`.")
        c1, c2 = st.columns([2, 3])
        ej = c1.selectbox("Ejemplos", [f"{destino}|{int(d_dest.anio.max())}-07", "Colima|2020-04", "municipio|06007"])
        id_oro = c2.text_input("Dato a rastrear", ej, key=f"id_{ej}")
        r = linaje.rastrear(id_oro.strip(), tabla_linaje(), limite=5) if id_oro else pd.DataFrame()
        if r.empty:
            st.warning("No encontré ese dato. Revisa el formato Destino|AAAA-MM.")
        else:
            st.dataframe(r[["fuente", "rol", "archivo_origen", "fila_origen", "fecha_ingesta"]].rename(columns={
                "fuente": "Fuente", "rol": "Qué se hizo", "archivo_origen": "Archivo", "fila_origen": "Fila",
                "fecha_ingesta": "Descargado"}), hide_index=True, width="stretch")

st.markdown("<div class='pie'>Observatorio de Ocupación Hotelera de Colima · Fuentes: SECTUR-DataTur (CC BY 4.0), "
            "Banco de México (SIE), INEGI (DENUE y Marco Geoestadístico). Elaboración propia; no representa una "
            "postura oficial de las instituciones. Dataset abierto en el repositorio del proyecto.</div>",
            unsafe_allow_html=True)
