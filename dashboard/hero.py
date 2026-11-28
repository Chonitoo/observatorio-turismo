"""Encabezado animado del tablero (HTML + CSS + JS dentro de un iframe de Streamlit).

Animaciones (inspiradas en referencias de Dribbble; implementación propia, sin recursos de terceros):
  * Fotos del destino que se alternan con fundido y zoom lento ("Ken Burns").
  * Logo propio (sol + olas) que se dibuja trazo a trazo y luego revela el nombre.
  * Título grande que sube línea por línea.
  * Etiquetas flotantes que se mecen suavemente sobre la foto.
  * Tarjetas de vidrio (glassmorphism) con números que cuentan desde cero.
Respeta `prefers-reduced-motion`: si el usuario lo pide, no hay movimiento.
"""
from __future__ import annotations

import base64
import json
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
FOTOS_DESTINO = {
    "Manzanillo": ["manzanillo_bahia_santiago.jpg", "manzanillo_desde_lo_alto.jpg"],
    "Colima": ["colima_volcan.jpg", "colima_jardin_libertad.jpg"],
}


@lru_cache(maxsize=8)
def _data_uri(nombre: str) -> str:
    return "data:image/jpeg;base64," + base64.b64encode((ASSETS / nombre).read_bytes()).decode()


@lru_cache(maxsize=1)
def creditos() -> list[dict]:
    return json.loads((ASSETS / "creditos.json").read_text(encoding="utf-8"))


def credito_fotos(destino: str) -> str:
    nombres = set(FOTOS_DESTINO.get(destino, []))
    return " · ".join(f"{c['autor']} ({c['licencia'][0]}, Wikimedia Commons)" for c in creditos()
                      if c["archivo"] in nombres)


def html(destino: str, subtitulo: str, kpis: list[dict], etiquetas: list[str], fecha: str) -> str:
    fotos = FOTOS_DESTINO.get(destino, [])
    capas = "".join(f'<div class="foto" style="background-image:url({_data_uri(f)});animation-delay:{i * 7}s"></div>'
                    for i, f in enumerate(fotos)) or '<div class="foto sin-foto"></div>'
    n_fotos = max(len(fotos), 1)
    tarjetas = "".join(
        f'<div class="kpi" style="animation-delay:{1.3 + i * .12:.2f}s">'
        f'<div class="k-et">{k["etiqueta"]}</div>'
        f'<div class="k-val"><span class="contador" data-valor="{k["valor"]}" data-dec="{k.get("dec", 0)}">0</span>'
        f'<span class="k-suf">{k.get("sufijo", "")}</span></div>'
        f'<div class="k-sub {k.get("tono", "")}">{k.get("sub", "")}</div></div>' for i, k in enumerate(kpis))
    flotantes = "".join(f'<div class="flota f{i}" style="animation-delay:{1.8 + i * .25:.2f}s,{2.4 + i * .25:.2f}s">'
                        f'{e}</div>' for i, e in enumerate(etiquetas[:3]))
    credito = credito_fotos(destino)
    lineas = ["Observatorio", f"Hotelero · {destino}"]
    titulo = "".join(f'<span class="linea"><span style="animation-delay:{.7 + i * .15:.2f}s">{t}</span></span>'
                     for i, t in enumerate(lineas))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,sans-serif;background:transparent;overflow:hidden}}
.hero{{position:relative;height:540px;border-radius:26px;overflow:hidden;color:#fff;
       background:#0C161B;box-shadow:0 20px 50px rgba(12,22,27,.35)}}
.foto{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;
       animation:kenburns {7 * n_fotos}s ease-in-out infinite}}
.foto:only-child{{animation:zoom 22s ease-in-out infinite alternate;opacity:1}}
.sin-foto{{opacity:1;background:radial-gradient(1200px 500px at 70% 20%,#3E6F88 0%,#15344C 45%,#0C161B 100%)}}
@keyframes kenburns{{0%{{opacity:0;transform:scale(1.02)}}8%{{opacity:1}}{100 / n_fotos:.0f}%{{opacity:1;transform:scale(1.12)}}
  {100 / n_fotos + 8:.0f}%{{opacity:0;transform:scale(1.14)}}100%{{opacity:0}}}}
@keyframes zoom{{from{{transform:scale(1.02)}}to{{transform:scale(1.14)}}}}
.velo{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(12,22,27,.55) 0%,rgba(12,22,27,.15) 40%,
       rgba(12,22,27,.85) 100%)}}
.intro{{position:absolute;inset:0;background:#0C161B;display:flex;align-items:center;justify-content:center;
        z-index:20;animation:salir .6s ease 1.15s forwards}}
@keyframes salir{{to{{opacity:0;visibility:hidden}}}}
.logo path,.logo circle{{fill:none;stroke:#EAF2F5;stroke-width:3;stroke-linecap:round;stroke-dasharray:160;
        stroke-dashoffset:160;animation:trazo 1s ease forwards}}
.logo circle{{stroke:#F2C14E;animation-delay:.05s}} .logo path:nth-child(2){{animation-delay:.25s}}
.logo path:nth-child(3){{animation-delay:.4s}}
@keyframes trazo{{to{{stroke-dashoffset:0}}}}
.barra{{position:absolute;top:22px;left:28px;right:28px;display:flex;align-items:center;justify-content:space-between;z-index:5;
        opacity:0;animation:aparece .7s ease 1.2s forwards}}
.marca{{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.02em}}
.marca svg circle{{stroke:#F2C14E}} .marca svg path{{stroke:#EAF2F5}}
.chip{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);backdrop-filter:blur(10px);
       border-radius:999px;padding:7px 14px;font-size:12.5px}}
.contenido{{position:absolute;left:44px;top:96px;z-index:4;max-width:640px}}
.linea{{display:block;overflow:hidden}}
.linea span{{display:inline-block;transform:translateY(110%);animation:sube .9s cubic-bezier(.2,.8,.2,1) forwards;
       font-size:54px;font-weight:900;line-height:1.02;letter-spacing:-.035em}}
@keyframes sube{{to{{transform:none}}}}
.sub{{margin-top:14px;font-size:16px;opacity:0;max-width:520px;line-height:1.5;color:#EAF2F5;
      animation:aparece .8s ease 1.15s forwards}}
@keyframes aparece{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.flota{{position:absolute;z-index:4;padding:9px 14px;border-radius:14px;font-size:13px;font-weight:600;
        background:rgba(255,255,255,.92);color:#0C161B;box-shadow:0 10px 25px rgba(0,0,0,.25);opacity:0;
        animation:aparece .7s ease forwards,mece 5s ease-in-out infinite}}
.f0{{right:56px;top:110px}} .f1{{right:200px;top:200px}} .f2{{right:70px;top:268px}}
@keyframes mece{{0%,100%{{translate:0 0}}50%{{translate:0 -9px}}}}
.kpis{{position:absolute;left:28px;right:28px;bottom:26px;display:grid;grid-template-columns:repeat(4,1fr);gap:14px;z-index:5}}
.kpi{{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(16px) saturate(140%);
      -webkit-backdrop-filter:blur(16px);border-radius:18px;padding:16px 18px;opacity:0;
      animation:aparece .7s cubic-bezier(.2,.8,.2,1) forwards;transition:transform .25s,background .25s}}
.kpi:hover{{transform:translateY(-4px);background:rgba(255,255,255,.16)}}
.k-et{{font-size:12.5px;color:#C9DCE3;font-weight:500}}
.k-val{{font-size:34px;font-weight:800;letter-spacing:-.03em;margin-top:4px}}
.k-suf{{font-size:18px;font-weight:700;margin-left:2px;color:#EAF2F5}}
.k-sub{{font-size:12px;margin-top:6px;color:#C9DCE3}} .k-sub.up{{color:#8FE3B5}} .k-sub.down{{color:#FFB4A2}}
.credito{{position:absolute;right:16px;bottom:6px;font-size:10px;color:rgba(255,255,255,.6);z-index:6}}
@media (max-width:980px){{.linea span{{font-size:40px}} .flota{{display:none}} .contenido{{left:28px;top:84px}}
  .kpis{{grid-template-columns:repeat(2,1fr);gap:10px}} .k-val{{font-size:26px}} .kpi{{padding:12px 14px}}
  .sub{{font-size:14px}} .barra .chip:last-child{{display:none}}}}
@media (prefers-reduced-motion:reduce){{*{{animation-duration:.01s!important;animation-iteration-count:1!important}}}}
</style></head><body>
<div class="hero">
  {capas}<div class="velo"></div>
  <div class="intro"><svg class="logo" width="110" height="110" viewBox="0 0 60 60">
    <circle cx="30" cy="22" r="10"/><path d="M6 40 Q15 33 24 40 T42 40 T56 40"/><path d="M10 49 Q19 42 28 49 T46 49"/>
  </svg></div>
  <div class="barra"><div class="marca"><svg width="28" height="28" viewBox="0 0 60 60" fill="none" stroke-width="4"
      stroke-linecap="round"><circle cx="30" cy="22" r="10"/><path d="M6 40 Q15 33 24 40 T42 40 T56 40"/>
      <path d="M10 49 Q19 42 28 49 T46 49"/></svg>Observatorio Hotelero</div>
    <div style="display:flex;gap:8px"><span class="chip">📅 Datos hasta {fecha}</span>
      <span class="chip">🔄 Se actualiza cada semana</span></div></div>
  <div class="contenido"><h1>{titulo}</h1><p class="sub">{subtitulo}</p></div>
  {flotantes}
  <div class="kpis">{tarjetas}</div>
  <div class="credito">{('Foto: ' + credito) if credito else ''}</div>
</div>
<script>
const fmt = (v, d) => v.toLocaleString('es-MX', {{minimumFractionDigits: d, maximumFractionDigits: d}});
document.querySelectorAll('.contador').forEach((el, i) => {{
  const fin = parseFloat(el.dataset.valor), dec = parseInt(el.dataset.dec || 0), dur = 1300, t0 = performance.now() + 1300 + i * 120;
  const paso = t => {{ const p = Math.min(Math.max((t - t0) / dur, 0), 1), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(fin * e, dec); if (p < 1) requestAnimationFrame(paso); }};
  requestAnimationFrame(paso);
}});
</script></body></html>"""
