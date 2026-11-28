"""Observatorio Hotelero de Colima — sistema de planeación para hoteleros.

Pestañas: Pronóstico · Mi hotel (benchmark + simulador de ingresos y personal) · Temporadas ·
Competencia · Mapa · Confiabilidad. Lo importante (indicadores y pronóstico) está en la primera vista.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python -m streamlit run dashboard/app.py
"""
from __future__ import annotations

import calendar
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))
import hero  # noqa: E402
from src.pipeline import linaje  # noqa: E402

ORO, PLATA, REP = RAIZ / "data" / "gold", RAIZ / "data" / "silver", RAIZ / "reports"

# Paleta inspirada en tonos de mar y atardecer (base #0C161B · #15344C · #3E6F88 · #5F95AF · #EAF2F5)
NOCHE, MAR, MAR2, CIELO, NIEBLA = "#0C161B", "#15344C", "#3E6F88", "#5F95AF", "#EAF2F5"
TEAL, SOL, CORAL, VERDE, GRIS, TINTA = "#0E7C86", "#F2B33D", "#E4572E", "#2E9E6B", "#C5CED8", "#13232F"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_L = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"]
COLOR_TIPO = {"Hotel": TEAL, "Motel": CORAL, "Departamento o casa amueblada": "#7A5CC7",
              "Cabañas y villas": VERDE, "Pensión o casa de huéspedes": SOL, "Campamento o albergue": CIELO}
TEMPORADA = {
    "Alta": {"color": TEAL, "fondo": "#E1F2F3", "icono": "🔥",
             "accion": "Sube tarifas, contrata personal eventual con 4 a 6 semanas de anticipación y asegura inventario."},
    "Media": {"color": "#B9861A", "fondo": "#FBF1D9", "icono": "⚖️",
              "accion": "Mantén la tarifa base y lanza promociones para fines de semana largos y puentes."},
    "Baja": {"color": CORAL, "fondo": "#FCE6DF", "icono": "🧊",
             "accion": "Promociones, convenios con empresas y escuelas, mantenimiento y vacaciones del personal."},
}

st.set_page_config(page_title="Observatorio Hotelero · Colima", page_icon="🏨", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"], .stMarkdown {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: linear-gradient(180deg, #EEF3F6 0%, #F7F9FB 420px); }}
.block-container {{ padding-top: 1rem; padding-bottom: 3rem; max-width: 1320px; }}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
h1, h2, h3 {{ color: {TINTA}; letter-spacing: -0.025em; }}
iframe {{ border-radius: 26px; }}

@keyframes aparece {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
.revela {{ animation: aparece .7s cubic-bezier(.2,.8,.2,1) both; }}
@supports (animation-timeline: view()) {{
  .scroll-revela {{ animation: aparece linear both; animation-timeline: view(); animation-range: entry 0% cover 25%; }}
}}

.paso {{ background: white; border-radius: 18px; padding: 16px 18px; border: 1px solid #E3EAF0;
        box-shadow: 0 4px 16px rgba(19,35,47,.05); display: flex; gap: 14px; align-items: center; }}
.paso .num {{ width: 38px; height: 38px; border-radius: 12px; background: {NOCHE}; color: white; font-weight: 800;
             display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.paso b {{ color: {TINTA}; }} .paso span {{ color: #5B6B7C; font-size: .88rem; }}

.card {{ background: white; border-radius: 20px; padding: 20px 22px; border: 1px solid #E3EAF0;
        box-shadow: 0 6px 22px rgba(19,35,47,.06); height: 100%; transition: transform .25s, box-shadow .25s; }}
.card:hover {{ transform: translateY(-3px); box-shadow: 0 14px 30px rgba(19,35,47,.10); }}
.card h4 {{ margin: 0 0 6px 0; font-size: 1rem; }} .card p {{ margin: 0; color: #3A4D60; font-size: .93rem; line-height: 1.5; }}
.card.bueno {{ border-top: 4px solid {VERDE}; }} .card.bueno h4 {{ color: {VERDE}; }}
.card.alerta {{ border-top: 4px solid {CORAL}; }} .card.alerta h4 {{ color: {CORAL}; }}
.card.oportunidad {{ border-top: 4px solid {TEAL}; }} .card.oportunidad h4 {{ color: {TEAL}; }}

.met {{ background: white; border-radius: 18px; padding: 16px 18px; border: 1px solid #E3EAF0;
       box-shadow: 0 4px 16px rgba(19,35,47,.05); height: 100%; }}
.met .et {{ font-size: .82rem; color: #5B6B7C; }} .met .v {{ font-size: 1.9rem; font-weight: 800; color: {TINTA};
           letter-spacing: -.03em; line-height: 1.15; }}
.met .s {{ font-size: .8rem; margin-top: 4px; font-weight: 600; }} .s.up {{ color: {VERDE}; }} .s.down {{ color: {CORAL}; }}
.s.neutral {{ color: #5B6B7C; }}
.met.oscura {{ background: linear-gradient(135deg, {NOCHE}, {MAR}); border: none; }}
.met.oscura .et {{ color: #A9C3CF; }} .met.oscura .v {{ color: white; }} .met.oscura .s {{ color: #8FE3B5; }}

.seccion {{ font-size: .76rem; font-weight: 800; color: {TEAL}; text-transform: uppercase; letter-spacing: .1em; }}
.titulo {{ font-size: 1.65rem; font-weight: 800; color: {TINTA}; letter-spacing: -.03em; margin: 2px 0 2px 0; }}
.subt {{ color: #5B6B7C; margin-bottom: 14px; }}
.reco {{ background: linear-gradient(90deg, #E6F4F4, #FFFFFF); border: 1px solid #CFE7E8; border-radius: 16px;
        padding: 14px 18px; margin: 10px 0; color: #24414F; }}
.reco b {{ color: {TEAL}; }}
.mes {{ border-radius: 16px; padding: 12px 8px; text-align: center; border: 2px solid transparent;
       transition: transform .2s; animation: aparece .6s ease both; }}
.mes:hover {{ transform: scale(1.04); }}
.mes .n {{ font-weight: 700; font-size: .92rem; color: {TINTA}; }} .mes .p {{ font-weight: 900; font-size: 1.45rem; }}
.mes .t {{ font-size: .7rem; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }}
.pie {{ color: #7A8796; font-size: .76rem; margin-top: 28px; border-top: 1px solid #E3EAF0; padding-top: 12px; }}

[data-testid="stTabs"] [role="tablist"] {{ gap: 6px; background: white; padding: 6px; border-radius: 999px;
    border: 1px solid #E3EAF0; box-shadow: 0 6px 20px rgba(19,35,47,.06); width: fit-content; margin: 6px auto 14px auto; }}
[data-testid="stTab"] {{ border-radius: 999px; padding: 9px 18px !important; height: auto !important; border: none;
    transition: background .2s; }}
[data-testid="stTab"] p {{ font-size: .95rem !important; font-weight: 600; color: #42566B; }}
[data-testid="stTab"]:not([aria-selected="true"]):hover {{ background: #EEF3F6; }}
[data-testid="stTab"]:not([aria-selected="true"]):focus, [data-testid="stTab"]:not([aria-selected="true"]):focus-visible
    {{ background: transparent; outline: none; box-shadow: none; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {NOCHE}; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: white !important; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"] {{ display: none; }}
div[data-testid="stForm"] {{ background: white; border-radius: 20px; border: 1px solid #E3EAF0; }}
</style>""", unsafe_allow_html=True)


# ============================================================================= datos
@st.cache_data
def cargar():
    o = pd.read_csv(ORO / "destino_mes.csv", low_memory=False)
    o["fecha"] = pd.to_datetime(o["periodo"])
    leer = lambda p: json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    return {
        "oro": o,
        "cat": pd.read_csv(ORO / "hotel_categoria_mes.csv", low_memory=False),
        "pron": pd.read_csv(ORO / "pronostico_destino_mes.csv"),
        "met": leer(REP / "E4" / "pronostico_metricas.json"),
        "mun": pd.read_csv(ORO / "municipio_hospedaje.csv", dtype={"cvegeo": str}),
        "est": pd.read_csv(ORO / "establecimientos_hospedaje.csv"),
        "calidad": leer(REP / "E1" / "calidad.json"), "faltantes": leer(REP / "E1" / "faltantes.json"),
        "linaje": leer(REP / "E2" / "linaje.json"), "geo": leer(REP / "E2" / "geoespacial.json"),
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
oro, pron_all = D["oro"], D["pron"]
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
    return pd.DataFrame({"ocupacion": g[["cuartos_ocupados", "cuartos_disponibles"]].apply(ocupacion),
                         "estadia": g[["turistas_noche", "llegadas"]].apply(estadia),
                         "extranjeros": g[["llegadas_no_residentes", "llegadas"]].apply(extranjeros)})


def dias(m: int, anio: int = 2025) -> int:
    return calendar.monthrange(anio, m)[1]


def seccion(eti, titulo, subt=""):
    st.markdown(f"<div class='scroll-revela'><div class='seccion'>{eti}</div><div class='titulo'>{titulo}</div>"
                f"<div class='subt'>{subt}</div></div>", unsafe_allow_html=True)


def met(col, etiqueta, valor, sub="", tono="neutral", oscura=False):
    col.markdown(f"<div class='met revela {'oscura' if oscura else ''}'><div class='et'>{etiqueta}</div>"
                 f"<div class='v'>{valor}</div><div class='s {tono}'>{sub}</div></div>", unsafe_allow_html=True)


def card(col, clase, titulo, texto, retraso=0.0):
    col.markdown(f"<div class='card {clase} revela' style='animation-delay:{retraso}s'><h4>{titulo}</h4>"
                 f"<p>{texto}</p></div>", unsafe_allow_html=True)


def reco(texto):
    st.markdown(f"<div class='reco scroll-revela'>✅ <b>Recomendación:</b> {texto}</div>", unsafe_allow_html=True)


def estilo(fig, alto=380, leyenda=True):
    fig.update_layout(height=alto, margin=dict(t=30, b=10, l=10, r=10), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="Inter, sans-serif", color=TINTA, size=13), showlegend=leyenda,
                      legend=dict(orientation="h", y=1.12, x=0, title=None),
                      hoverlabel=dict(font_family="Inter, sans-serif"), transition_duration=500)
    fig.update_xaxes(showgrid=False, linecolor="#D9E0E8")
    fig.update_yaxes(gridcolor="#EEF1F5", zeroline=False)
    return fig


CFG = {"displayModeBar": False}

# ============================================================================= selección de destino
destinos = sorted(oro.centro.unique())
c1, c2, c3 = st.columns([1.3, 3, 1.3], vertical_alignment="center")
with c1:
    destino = st.selectbox("📍 Destino", destinos, index=destinos.index("Manzanillo"),
                           help="Todo el sistema se ajusta al destino que elijas.")
d_dest = oro[oro.centro == destino]
pron = pron_all[pron_all.centro == destino].sort_values("periodo").reset_index(drop=True)
met_dest = D["met"]["por_destino"].get(destino, {})
ANIO_D = int(d_dest.anio.max())
a, b = d_dest[d_dest.anio == ANIO_D], d_dest[d_dest.anio == ANIO_D - 1]
pre = d_dest[d_dest.periodo_covid == "Prepandemia"]
es_playa = d_dest.tipo_centro.iloc[0] == "Centros de Playa"
grupo_base = oro[(oro.litoral == d_dest.litoral.iloc[0]) if es_playa else (oro.tipo_centro == "Ciudades")]
rk = resumen(grupo_base[grupo_base.periodo_covid == "Pospandemia"], "centro").sort_values("ocupacion", ascending=False)
pos = list(rk.index).index(destino) + 1

# --- plan con el pronóstico (temporada relativa al destino)
disp_noche = (d_dest[d_dest.periodo_covid == "Pospandemia"].groupby("mes")["cuartos_disponibles"].mean()
              / pd.Series({m: dias(m) for m in range(1, 13)}))
plan = pron.assign(mes=pron.mes.astype(int)).set_index("mes")
plan["vacios_noche"] = disp_noche.reindex(plan.index) * (1 - plan.pronostico_pct / 100)
plan["temporada"] = pd.cut(plan.pronostico_pct.rank(method="first"), [0, 4, 8, 12],
                           labels=["Baja", "Media", "Alta"]).astype(str)
prox = pron.iloc[0]
mejor_m, peor_m = int(plan.pronostico_pct.idxmax()), int(plan.pronostico_pct.idxmin())
ocup_act, ocup_prev = ocupacion(a), ocupacion(b)
dif = ocup_act - ocup_prev

with c3:
    plan_csv = plan.reset_index()[["periodo", "pronostico_pct", "li80", "ls80", "vacios_noche", "temporada"]].round(1)
    plan_csv["accion_recomendada"] = [TEMPORADA[t]["accion"] for t in plan_csv.temporada]
    st.download_button("⬇️ Descargar plan del año", plan_csv.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"plan_{destino.lower().replace(' ', '_')}.csv", mime="text/csv",
                       width="stretch")

# ============================================================================= HERO (primera vista)
kpis = [
    {"etiqueta": f"Ocupación {ANIO_D}", "valor": round(ocup_act, 1), "dec": 1, "sufijo": "%",
     "sub": f"{'▲' if dif >= 0 else '▼'} {abs(dif):.1f} pts vs {ANIO_D - 1}", "tono": "up" if dif >= 0 else "down"},
    {"etiqueta": f"Pronóstico {MESES_L[int(prox.mes) - 1]} {int(prox.anio)}", "valor": round(prox.pronostico_pct, 1),
     "dec": 1, "sufijo": "%", "sub": f"rango {prox.li80:.0f}–{prox.ls80:.0f}%"},
    {"etiqueta": f"Promedio pronosticado {int(prox.anio)}", "valor": round(pron.pronostico_pct.mean(), 1), "dec": 1,
     "sufijo": "%", "sub": f"mejor mes: {MESES_L[mejor_m - 1]}"},
    {"etiqueta": "Lugar en su grupo", "valor": pos, "sufijo": f"º de {len(rk)}",
     "sub": f"líder: {rk.index[0] if rk.index[0] != destino else rk.index[1]}"},
]
etiquetas = [f"🔥 Temporada alta: {MESES_L[mejor_m - 1]}", f"🧊 Mes más flojo: {MESES_L[peor_m - 1]}",
             f"✈️ {extranjeros(a):.0f}% turistas extranjeros"]
st.iframe(hero.html(destino, "Pronóstico, temporadas y competencia del destino, más un simulador de ingresos "
                    "y personal para tu hotel. Datos oficiales de SECTUR, Banxico e INEGI.", kpis, etiquetas,
                    f"{MESES_L[MES_MAX - 1]} {ANIO_MAX}"), height=548)   # HTML propio y fijo (no viene del usuario)

# ============================================================================= cómo funciona
cols = st.columns(3)
pasos = [("1", "Elige tu destino", "arriba a la izquierda; todo se ajusta solo."),
         ("2", "Revisa el pronóstico", "cuánto se va a llenar cada mes del próximo año."),
         ("3", "Planea con «Mi hotel»", "escribe tus cuartos y tarifa: ingresos y personal por mes.")]
for i, (col, (n, t, s)) in enumerate(zip(cols, pasos)):
    col.markdown(f"<div class='paso revela' style='animation-delay:{.15 * i:.2f}s'><div class='num'>{n}</div>"
                 f"<div><b>{t}</b><br><span>{s}</span></div></div>", unsafe_allow_html=True)
st.write("")

# ============================================================================= insights
cols = st.columns(3)
rec = ocup_act - ocupacion(pre)
card(cols[0], "bueno", "👍 Lo bueno",
     f"{destino} {'ya supera' if rec > 0 else 'aún no recupera'} su nivel prepandemia: <b>{ocup_act:.0f}%</b> en "
     f"{ANIO_D} contra <b>{ocupacion(pre):.0f}%</b> en 2016-2019.", 0)
card(cols[1], "alerta", "⚠️ Lo preocupante",
     f"Cada turista se queda <b>{estadia(a):.1f} noches</b> (antes {estadia(pre):.1f}) y sólo <b>{extranjeros(a):.0f} "
     f"de cada 100</b> son extranjeros.", .12)
card(cols[2], "oportunidad", "💡 La oportunidad",
     f"En <b>{MESES_L[peor_m - 1]}</b> se esperan unos <b>{plan.vacios_noche[peor_m]:,.0f} cuartos vacíos cada noche</b>. "
     f"Llenar sólo el 10 % de ellos es una oportunidad concreta de venta.", .24)
st.write("")

tabs = st.tabs(["🔮 Pronóstico", "🏨 Mi hotel", "🗓️ Temporadas", "🌊 Competencia", "🗺️ Mapa", "🛡️ Confiabilidad"])

# ============================================================================= PRONÓSTICO
with tabs[0]:
    seccion("Pronóstico", f"¿Cuánto se va a llenar {destino} en {int(prox.anio)}?",
            f"Pronóstico mes a mes con su rango probable. Los datos oficiales más recientes son de "
            f"{MESES_L[MES_MAX - 1]} {ANIO_MAX}, por eso el pronóstico cubre {int(prox.anio)}.")
    c = st.columns(4)
    prom_pron = pron.pronostico_pct.mean()
    met(c[0], f"Promedio esperado {int(prox.anio)}", f"{prom_pron:.1f}%",
        f"{prom_pron - ocup_act:+.1f} pts vs {ANIO_D}", "up" if prom_pron >= ocup_act else "down", oscura=True)
    met(c[1], "Mejor mes", MESES_L[mejor_m - 1].capitalize(), f"{plan.pronostico_pct[mejor_m]:.0f}% esperado")
    met(c[2], "Mes más flojo", MESES_L[peor_m - 1].capitalize(), f"{plan.pronostico_pct[peor_m]:.0f}% esperado", "down")
    err = met_dest.get("modelo" if met_dest.get("metodo_publicado", "").startswith("SARIMAX") else "ingenuo", {})
    met(c[3], "Precisión probada", f"±{err.get('mae', 0):.1f} pts",
        "error promedio al pronosticar el último año real")
    st.write("")
    hist = d_dest[d_dest.fecha >= f"{ANIO_D - 2}-01-01"]
    fut = pron.assign(fecha=pd.to_datetime(pron.periodo))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(fut.fecha) + list(fut.fecha[::-1]), y=list(fut.ls95) + list(fut.li95[::-1]),
                             fill="toself", fillcolor="rgba(95,149,175,.15)", line=dict(width=0),
                             name="Rango posible (95 %)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=list(fut.fecha) + list(fut.fecha[::-1]), y=list(fut.ls80) + list(fut.li80[::-1]),
                             fill="toself", fillcolor="rgba(14,124,134,.22)", line=dict(width=0),
                             name="Rango probable (80 %)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=hist.fecha, y=hist.ocupacion_pct, name="Real", mode="lines+markers",
                             line=dict(color=NOCHE, width=2.5), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=fut.fecha, y=fut.pronostico_pct, name="Pronóstico", mode="lines+markers+text",
                             line=dict(color=TEAL, width=3.5, dash="dot"), marker=dict(size=7),
                             text=[f"{v:.0f}%" for v in fut.pronostico_pct], textposition="top center",
                             textfont=dict(size=11, color=TEAL)))
    corte = (fut.fecha.iloc[0] - pd.DateOffset(days=15)).strftime("%Y-%m-%d")
    fig.add_shape(type="line", x0=corte, x1=corte, y0=0, y1=1, yref="paper", line=dict(dash="dash", color="#9AA9B8"))
    fig.add_annotation(x=fut.fecha.iloc[0], y=98, text="pronóstico →", showarrow=False, font=dict(color="#5B6B7C"),
                       xanchor="left")
    fig.update_yaxes(title="% de cuartos ocupados", ticksuffix="%", range=[0, 100])
    st.plotly_chart(estilo(fig, 430), width="stretch", config=CFG)
    st.caption(f"Método: {met_dest.get('metodo_publicado', '')}. Se eligió por validación: al pronosticar el último "
               f"año real, este método se equivocó en promedio ±{err.get('mae', 0):.1f} puntos. "
               "La banda indica dónde es probable que caiga la ocupación real.")
    reco(f"Prepárate para <b>{MESES_L[mejor_m - 1]}</b> (≈{plan.pronostico_pct[mejor_m]:.0f}%) desde "
         f"{MESES_L[(mejor_m - 3) % 12]}: personal eventual y tarifas. Para <b>{MESES_L[peor_m - 1]}</b> "
         f"(≈{plan.pronostico_pct[peor_m]:.0f}%) arma promociones con un mes de anticipación.")

# ============================================================================= MI HOTEL + SIMULADOR
with tabs[1]:
    seccion("Mi hotel", "Tu hotel contra tu competencia, y lo que puedes esperar cada mes",
            "Escribe los datos básicos de tu hotel. No se guardan: sólo se usan para calcular en esta pantalla.")
    cats_dest = D["cat"][(D["cat"].centro == destino) & (D["cat"].periodo_covid == "Pospandemia")]
    categorias = [c for c in ["1 estrella", "2 estrellas", "3 estrellas", "4 estrellas", "5 estrellas", "Sin categoría"]
                  if c in set(cats_dest.categoria)]
    f1, f2, f3, f4 = st.columns(4)
    categoria = f1.selectbox("Categoría de tu hotel", categorias,
                             index=categorias.index("4 estrellas") if "4 estrellas" in categorias else 0)
    cuartos = f2.number_input("Número de cuartos", 5, 2000, 60, step=5)
    tarifa = f3.number_input("Tarifa promedio por noche (MXN)", 200, 50000, 1800, step=100)
    ratio = f4.number_input("Cuartos que limpia una camarista por turno", 8, 25, 14,
                            help="Referencia común en hotelería: entre 12 y 16 cuartos por turno.")
    usar_propia = st.toggle("Conozco la ocupación promedio de mi hotel (ajusta el cálculo a tu hotel)")
    propia = st.slider("Ocupación promedio de tu hotel en el último año (%)", 5, 100, 55) if usar_propia else None

    oc_cat = (cats_dest[cats_dest.categoria == categoria].groupby("mes")
              .apply(lambda x: (x.ocupacion_pct * x.cuartos_disponibles).sum() / x.cuartos_disponibles.sum(),
                     include_groups=False))
    oc_dest = resumen(d_dest[d_dest.periodo_covid == "Pospandemia"], "mes")["ocupacion"]
    factor = (oc_cat / oc_dest).reindex(range(1, 13)).fillna(1.0)
    prom_cat = float((oc_cat * pd.Series({m: dias(m) for m in range(1, 13)})).sum() / 365) if len(oc_cat) else ocup_act
    ajuste = (propia / prom_cat) if propia else 1.0
    yo = plan[["periodo", "pronostico_pct", "li80", "ls80", "temporada"]].copy()
    for col_ in ["pronostico_pct", "li80", "ls80"]:
        yo[col_] = (yo[col_] * factor.reindex(yo.index) * ajuste).clip(0, 100)
    yo["dias"] = [dias(m, int(prox.anio)) for m in yo.index]
    yo["ocupados_noche"] = cuartos * yo.pronostico_pct / 100
    yo["ingreso"] = yo.ocupados_noche * yo.dias * tarifa
    yo["camaristas"] = [math.ceil(x / ratio) for x in yo.ocupados_noche]
    ingreso_anual = yo.ingreso.sum()
    pesimista = (cuartos * yo.li80 / 100 * yo.dias * tarifa).sum()
    optimista = (cuartos * yo.ls80 / 100 * yo.dias * tarifa).sum()

    st.write("")
    c = st.columns(4)
    diff_cat = (propia - prom_cat) if propia else (prom_cat - ocup_act)
    met(c[0], f"Ocupación típica {categoria} en {destino}", f"{prom_cat:.0f}%",
        (f"tú: {propia}% ({diff_cat:+.0f} pts)" if propia else f"{diff_cat:+.0f} pts vs el destino"),
        "up" if diff_cat >= 0 else "down")
    met(c[1], f"Ingreso esperado {int(prox.anio)}", f"${ingreso_anual / 1e6:,.1f} M",
        f"rango ${pesimista / 1e6:,.1f}–{optimista / 1e6:,.1f} M", oscura=True)
    met(c[2], "Mes de mayor ingreso", MESES_L[int(yo.ingreso.idxmax()) - 1].capitalize(),
        f"${yo.ingreso.max() / 1e3:,.0f} mil")
    met(c[3], "Camaristas necesarias", f"{yo.camaristas.min()}–{yo.camaristas.max()}",
        f"pico en {MESES_L[int(yo.camaristas.idxmax()) - 1]}")
    st.write("")

    cg1, cg2 = st.columns([1.6, 1])
    with cg1:
        fig = go.Figure()
        fig.add_bar(x=[MESES[m - 1] for m in yo.index], y=yo.ingreso / 1e3, name="Ingreso esperado (miles MXN)",
                    marker_color=[TEMPORADA[t]["color"] for t in yo.temporada], opacity=.9,
                    hovertemplate="%{x}: $%{y:,.0f} mil<extra></extra>")
        fig.add_trace(go.Scatter(x=[MESES[m - 1] for m in yo.index], y=yo.pronostico_pct, name="Ocupación esperada %",
                                 yaxis="y2", mode="lines+markers", line=dict(color=NOCHE, width=2.5)))
        fig.update_layout(yaxis=dict(title="miles de MXN"), yaxis2=dict(title="% ocupación", overlaying="y",
                          side="right", range=[0, 100], dtick=20, ticksuffix="%", showgrid=False))
        st.plotly_chart(estilo(fig, 380), width="stretch", config=CFG)
    with cg2:
        tabla = pd.DataFrame({"Mes": [MESES_L[m - 1].capitalize() for m in yo.index],
                              "Ocupación": [f"{v:.0f}%" for v in yo.pronostico_pct],
                              "Cuartos/noche": [f"{v:.0f}" for v in yo.ocupados_noche],
                              "Camaristas": yo.camaristas.values,
                              "Ingreso": [f"${v:,.0f}" for v in yo.ingreso]})
        st.dataframe(tabla, hide_index=True, width="stretch", height=380)

    st.markdown("<div class='seccion scroll-revela' style='margin-top:10px'>Simulador</div>"
                "<div class='titulo' style='font-size:1.3rem'>¿Qué pasa si…?</div>"
                "<div class='subt'>Mueve los controles para probar estrategias. Tú defines los supuestos: el sistema no "
                "asume cómo reaccionan los clientes a un cambio de precio.</div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    t_alta = s1.slider("Cambio de tarifa en temporada alta (%)", -20, 40, 10, 5)
    t_baja = s2.slider("Cambio de tarifa en temporada baja (%)", -40, 20, -15, 5)
    extra = s3.slider("Puntos extra de ocupación en temporada baja (promociones)", 0, 20, 5)
    sim = yo.copy()
    sim["tarifa"] = tarifa * sim.temporada.map({"Alta": 1 + t_alta / 100, "Baja": 1 + t_baja / 100, "Media": 1.0})
    sim["ocup"] = (sim.pronostico_pct + sim.temporada.map({"Baja": extra}).fillna(0)).clip(0, 100)
    sim["ingreso_sim"] = cuartos * sim.ocup / 100 * sim.dias * sim.tarifa
    delta = sim.ingreso_sim.sum() - ingreso_anual
    c = st.columns([1, 2.2])
    met(c[0], "Ingreso anual con tu estrategia", f"${sim.ingreso_sim.sum() / 1e6:,.2f} M",
        f"{'▲' if delta >= 0 else '▼'} ${abs(delta) / 1e3:,.0f} mil vs escenario base ({delta / ingreso_anual:+.1%})",
        "up" if delta >= 0 else "down", oscura=True)
    with c[1]:
        fig = go.Figure()
        fig.add_bar(x=[MESES[m - 1] for m in sim.index], y=yo.ingreso / 1e3, name="Base", marker_color=GRIS)
        fig.add_bar(x=[MESES[m - 1] for m in sim.index], y=sim.ingreso_sim / 1e3, name="Con tu estrategia",
                    marker_color=TEAL)
        fig.update_layout(barmode="group", yaxis_title="miles de MXN")
        st.plotly_chart(estilo(fig, 280), width="stretch", config=CFG)
    st.download_button("⬇️ Descargar mi proyección (Excel/CSV)",
                       sim.reset_index()[["periodo", "temporada", "ocup", "tarifa", "camaristas", "ingreso_sim"]]
                       .rename(columns={"ocup": "ocupacion_pct", "ingreso_sim": "ingreso_mxn"}).round(1)
                       .to_csv(index=False).encode("utf-8-sig"), file_name="mi_hotel_proyeccion.csv", mime="text/csv")
    st.caption("Cálculo: ocupación pronosticada del destino × diferencia típica de tu categoría (2022 en adelante) "
               "× tu ajuste opcional; ingreso = cuartos × ocupación × días × tarifa; camaristas = cuartos ocupados por "
               "noche ÷ cuartos por camarista. Es una estimación para planear, no una garantía.")

# ============================================================================= TEMPORADAS
with tabs[2]:
    seccion("Temporadas", f"¿Qué hago cada mes en {destino}?",
            f"Calendario {int(prox.anio)} con el pronóstico. La temporada es relativa al destino: sus 4 meses más "
            "fuertes, los intermedios y los 4 más débiles.")
    for fila in (range(1, 7), range(7, 13)):
        cols = st.columns(6)
        for j, (col, m) in enumerate(zip(cols, fila)):
            t = TEMPORADA[plan.temporada[m]]
            col.markdown(f"<div class='mes' style='background:{t['fondo']};border-color:{t['color']}33;"
                         f"animation-delay:{(m - 1) * .05:.2f}s'><div class='n'>{MESES[m - 1]}</div>"
                         f"<div class='p' style='color:{t['color']}'>{plan.pronostico_pct[m]:.0f}%</div>"
                         f"<div class='t' style='color:{t['color']}'>{t['icono']} {plan.temporada[m]}</div></div>",
                         unsafe_allow_html=True)
        st.write("")
    cA, cB = st.columns([1, 1.6])
    with cA:
        sel = st.selectbox("Elige un mes", list(range(1, 13)), format_func=lambda m: MESES_L[m - 1].capitalize(),
                           index=peor_m - 1)
        t = TEMPORADA[plan.temporada[sel]]
        st.markdown(f"<div class='card revela' style='border-top:4px solid {t['color']}'>"
                    f"<h4 style='color:{t['color']}'>{t['icono']} {MESES_L[sel - 1].capitalize()}: temporada "
                    f"{plan.temporada[sel].lower()}</h4><p>Ocupación esperada: <b>{plan.pronostico_pct[sel]:.0f}%</b> "
                    f"(probable entre {plan.li80[sel]:.0f}% y {plan.ls80[sel]:.0f}%).<br>Cuartos vacíos esperados cada "
                    f"noche en el destino: <b>{plan.vacios_noche[sel]:,.0f}</b>.</p></div>", unsafe_allow_html=True)
        reco(t["accion"])
    with cB:
        fig = go.Figure(go.Bar(x=MESES, y=plan.pronostico_pct, marker_color=[TEMPORADA[x]["color"] for x in plan.temporada],
                               marker_line_width=[3 if m == sel else 0 for m in plan.index], marker_line_color=NOCHE,
                               error_y=dict(type="data", symmetric=False, array=plan.ls80 - plan.pronostico_pct,
                                            arrayminus=plan.pronostico_pct - plan.li80, color="#9AA9B8", thickness=1),
                               text=[f"{v:.0f}%" for v in plan.pronostico_pct], textposition="outside",
                               hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
        fig.update_yaxes(ticksuffix="%", range=[0, 100], title="% esperado")
        st.plotly_chart(estilo(fig, 360, leyenda=False), width="stretch", config=CFG)

# ============================================================================= COMPETENCIA
with tabs[3]:
    grupo_txt = f"destinos de playa del {d_dest.litoral.iloc[0]}" if es_playa else "ciudades monitoreadas"
    seccion("Competencia", f"¿Cómo va {destino} contra los {grupo_txt}?", "Promedio después de la pandemia (2022 en adelante).")
    res = rk.sort_values("ocupacion")
    lider = res.index[-1]
    yo_r = res.loc[destino]
    c = st.columns(3)
    met(c[0], "Lugar en ocupación", f"{pos}.º de {len(res)}", oscura=True)
    met(c[1], f"Distancia con {lider}" if lider != destino else "Posición",
        f"{res.ocupacion[lider] - yo_r.ocupacion:.0f} pts" if lider != destino else "Líder")
    met(c[2], "Noches por turista", f"{yo_r.estadia:.1f}", f"máximo del grupo: {res.estadia.max():.1f}")
    st.write("")
    fig = go.Figure(go.Bar(y=res.index, x=res.ocupacion, orientation="h",
                           marker_color=[TEAL if i == destino else GRIS for i in res.index],
                           text=[f"{v:.0f}%" for v in res.ocupacion], textposition="outside",
                           hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.update_xaxes(ticksuffix="%", range=[0, res.ocupacion.max() + 12])
    st.plotly_chart(estilo(fig, 28 * len(res) + 80, leyenda=False), width="stretch", config=CFG)
    lid3 = res.tail(3)
    reco(f"Los tres líderes ({', '.join(lid3.index[::-1])}) reciben <b>{lid3.extranjeros.mean():.0f}% de turistas "
         f"extranjeros</b> y retienen <b>{lid3.estadia.mean():.1f} noches</b>; {destino}: {yo_r.extranjeros:.0f}% y "
         f"{yo_r.estadia:.1f}. Turismo internacional y paquetes de estancia larga son la palanca principal.")

# ============================================================================= MAPA
with tabs[4]:
    mun, est = D["mun"], D["est"]
    top = mun.sort_values("establecimientos").iloc[-1]
    seccion("Mapa", "¿Dónde está la oferta de hospedaje en Colima?",
            f"{len(est)} lugares registrados en el DENUE del INEGI ({D['geo'].get('edicion_denue', '')}), incluidos "
            "departamentos y cabañas que no aparecen en las estadísticas de ocupación.")
    c = st.columns(4)
    met(c[0], "Lugares para hospedarse", f"{len(est)}", oscura=True)
    met(c[1], f"En {top.nomgeo}", f"{top.pct_oferta_estatal:.0f}%")
    met(c[2], "Departamentos, casas y cabañas",
        f"{est.tipo_alojamiento.isin(['Departamento o casa amueblada', 'Cabañas y villas']).sum()}")
    met(c[3], "Negocios de menos de 10 personas", f"{100 * (est.tamano == 'Micro').mean():.0f}%")
    st.write("")
    tipos = st.multiselect("Mostrar", list(COLOR_TIPO), default=list(COLOR_TIPO))
    fig = px.choropleth_map(mun, geojson=geo_municipios(), locations="cvegeo", featureidkey="properties.cvegeo",
                            color="establecimientos", color_continuous_scale=["#F5F7FA", "#9FB3C8"], opacity=.55,
                            hover_name="nomgeo", hover_data={"cvegeo": False, "establecimientos": True},
                            map_style="carto-positron", center={"lat": 19.05, "lon": -104.0}, zoom=8.75)
    for tipo, sub in est[est.tipo_alojamiento.isin(tipos)].groupby("tipo_alojamiento"):
        fig.add_trace(go.Scattermap(lat=sub.latitud, lon=sub.longitud, mode="markers", name=tipo,
                                    marker=dict(size=sub.tamano.map({"Micro": 8, "Pequeño": 12, "Mediano": 17,
                                                                     "Grande": 23}).to_numpy(),
                                                color=COLOR_TIPO[tipo], opacity=.9),
                                    text=sub.tipo_alojamiento + " · " + sub.per_ocu + " · " + sub.municipio_espacial,
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False,
                      legend=dict(orientation="h", y=-0.03))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": True})
    st.caption("Tamaño del punto = personas que trabajan ahí. Fuente: INEGI, DENUE; elaboración propia.")

# ============================================================================= CONFIABILIDAD
with tabs[5]:
    cal, lin, fal = D["calidad"], D["linaje"], D["faltantes"]
    total = sum(p["registros_entrada"] for p in cal["puertas"] if "entrada" in p["etapa"])
    seccion("Confiabilidad", "¿Puedo confiar en estos números?",
            "Datos oficiales, revisados automáticamente y rastreables hasta su archivo original.")
    c = st.columns(4)
    met(c[0], "Fuentes oficiales", "3", "SECTUR · Banxico · INEGI", oscura=True)
    met(c[1], "Registros revisados", f"{total:,}")
    met(c[2], "Con errores (apartados)", f"{cal['cuarentena_total']}")
    met(c[3], "Rastreables a su origen",
        f"{100 * (lin['ids_oro'] - lin['registros_oro_sin_linaje']) / lin['ids_oro']:.0f}%")
    st.write("")
    c = st.columns(3)
    card(c[0], "oportunidad", "🔄 Se actualiza solo",
         "Cada semana descarga los datos nuevos de las fuentes oficiales, los limpia, los revisa, rehace el pronóstico "
         "y actualiza este sistema.")
    card(c[1], "bueno", "✅ Revisado antes de mostrar",
         f"Aparta registros imposibles; estima meses aislados faltantes ({fal['huecos_imputados']} casos) y no inventa "
         "datos donde una categoría no existía. El pronóstico se valida contra el último año real.", .1)
    card(c[2], "alerta", "📌 Qué tener en cuenta",
         "La ocupación cubre hoteles registrados ante la Secretaría de Turismo; no incluye renta vacacional. "
         "Los pronósticos son estimaciones con un rango, no garantías.", .2)
    with st.expander("🔎 Para auditores: rastrear un dato hasta su archivo original"):
        c1_, c2_ = st.columns([2, 3])
        ej = c1_.selectbox("Ejemplos", [f"{destino}|{ANIO_D}-07", "Colima|2020-04", "municipio|06007"])
        id_oro = c2_.text_input("Dato a rastrear (Destino|AAAA-MM)", ej, key=f"id_{ej}")
        r = linaje.rastrear(id_oro.strip(), tabla_linaje(), limite=5) if id_oro else pd.DataFrame()
        if r.empty:
            st.warning("No encontré ese dato. Revisa el formato Destino|AAAA-MM.")
        else:
            st.dataframe(r[["fuente", "rol", "archivo_origen", "fila_origen", "fecha_ingesta"]], hide_index=True,
                         width="stretch")

cred = hero.credito_fotos(destino)
st.markdown(f"<div class='pie'>Observatorio de Ocupación Hotelera de Colima · Fuentes: SECTUR-DataTur (CC BY 4.0), "
            f"Banco de México (SIE), INEGI (DENUE y Marco Geoestadístico). Elaboración propia; no representa una "
            f"postura oficial de las instituciones.{(' Fotos: ' + cred + '.') if cred else ''}</div>",
            unsafe_allow_html=True)
