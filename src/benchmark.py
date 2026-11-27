"""Benchmark reproducible del pipeline Bronce → Plata → Oro (E3).

Uso:
    python -m src.benchmark --ab d8ba5e4 --repeticiones 7   # A/B intercalado: versión anterior vs. actual
    python -m src.benchmark --comparar                      # genera reports/E3/comparativa.json y .md
    python -m src.benchmark --etiqueta prueba --repeticiones 3   # sólo la versión actual

El modo --ab crea un git worktree temporal con la versión anterior y alterna las corridas
(A, B, A, B, ...) para que ambas versiones se midan bajo las mismas condiciones de la máquina.

Qué mide (cada repetición corre en un proceso nuevo, para que no haya caché entre corridas):
  * Tiempo   — tiempo de pared total del pipeline, SIN instrumentación (mediana de N corridas).
               El desglose por etapa sale de una corrida adicional con cProfile (que infla los
               tiempos), por eso se reporta también como porcentaje del total instrumentado.
  * Memoria  — pico de memoria del proceso (RSS máximo del SO, corridas limpias) y pico de
               asignaciones de Python (tracemalloc, corrida instrumentada), en MB.
  * Errores  — advertencias emitidas durante la ejecución (por tipo), registros que el propio
               pipeline genera y luego rechaza (p. ej. imputaciones inválidas), registros en
               cuarentena tardía (detectados hasta Oro), y archivos de salida que cambian al
               repetir la corrida SIN datos nuevos (no determinismo → commits espurios).
  * Salidas  — tamaño en disco de Plata, Oro y cuarentena.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "reports" / "E3"
CARPETAS_SALIDA = ["data/silver", "data/gold", "data/quarantine"]
N_PERFIL = 3   # corridas instrumentadas por versión (cProfile + tracemalloc); se reporta la mediana

# Funciones del pipeline cuyo tiempo acumulado se reporta como "etapa"
ETAPAS = {
    "lectura_bronce": ["leer_datatur", "leer_tipo_cambio", "leer_inpc", "leer_denue", "leer_municipios"],
    "puertas_calidad": ["puerta"],
    "faltantes": ["diagnostico", "imputar_explicitos", "imputar_huecos"],
    "integracion": ["agregar_destino", "integrar", "tipo_cambio_mensual", "inflacion_mensual"],
    "atipicos": ["detectar"],
    "transformacion": ["agregar_jerarquias", "discretizar", "normalizar", "seleccion_variables"],
    "geoespacial": ["union_espacial", "municipal", "enriquecer"],
    "linaje": ["construir", "verificar"],
    "escritura": ["to_csv", "to_file", "to_parquet"],
}

HIJO = r"""
import cProfile, json, pstats, sys, time, warnings
sys.path.insert(0, {raiz!r})
PERFILAR = {perfilar!r}
warnings.simplefilter("always")
avisos = []
warnings.showwarning = lambda m, c, f, l, *a, **k: avisos.append((c.__name__, str(m)[:120], f.split("site-packages")[-1][-60:], l))
if PERFILAR:
    import tracemalloc; tracemalloc.start()
from src.pipeline import ejecutar
prof = cProfile.Profile() if PERFILAR else None
t0 = time.perf_counter()
if prof: prof.enable()
ejecutar.main()
if prof: prof.disable()
t = time.perf_counter() - t0
import psutil
mi = psutil.Process().memory_info()
pico_rss = getattr(mi, "peak_wset", None)
if pico_rss is None:
    import resource
    pico_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
res = {{"tiempo_s": t, "pico_rss_mb": pico_rss / 2**20, "avisos": avisos}}
if PERFILAR:
    res["pico_python_mb"] = tracemalloc.get_traced_memory()[1] / 2**20
    funcs = {{}}
    for (archivo, linea, nombre), (cc, nc, tt, ct, _) in pstats.Stats(prof).stats.items():
        funcs[nombre] = max(funcs.get(nombre, 0.0), ct)
    res["funciones"] = funcs
print("@@RESULTADO@@" + json.dumps(res))
"""


def _huellas(raiz: Path = RAIZ) -> dict[str, str]:
    out = {}
    for c in CARPETAS_SALIDA:
        for f in sorted((raiz / c).rglob("*")):
            if f.is_file():
                out[f.relative_to(raiz).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def _tamanos(raiz: Path = RAIZ) -> dict[str, float]:
    return {c: round(sum(f.stat().st_size for f in (raiz / c).rglob("*") if f.is_file()) / 2**20, 2)
            for c in CARPETAS_SALIDA}


def _una_corrida(perfilar: bool = False, raiz: Path = RAIZ) -> dict:
    p = subprocess.run([sys.executable, "-c", HIJO.format(raiz=str(raiz), perfilar=perfilar)], cwd=raiz,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    linea = next((l for l in p.stdout.splitlines() if l.startswith("@@RESULTADO@@")), None)
    if p.returncode != 0 or linea is None:
        raise RuntimeError(f"El pipeline falló:\n{p.stderr[-3000:]}")
    return json.loads(linea.removeprefix("@@RESULTADO@@"))


def _errores_de_datos(raiz: Path = RAIZ) -> dict:
    cal = json.loads((raiz / "reports" / "E1" / "calidad.json").read_text(encoding="utf-8"))
    por_etapa = {p["etapa"] + "/" + p["fuente"]: p["registros_cuarentena"] for p in cal["puertas"]}
    generados = sum(v for k, v in por_etapa.items() if k.startswith("2_plata"))  # creados por el pipeline
    tardios = sum(v for k, v in por_etapa.items() if k.startswith("3_oro"))
    return {"cuarentena_por_puerta": por_etapa,
            "registros_invalidos_generados_por_el_pipeline": generados,
            "errores_detectados_hasta_oro": tardios}


def _corridas(raiz: Path, repeticiones: int, etiqueta: str):
    """Generador: hace una corrida limpia por llamada y acumula huellas para detectar no determinismo."""
    estado = {"corridas": [], "huellas": None, "espurios": []}
    for i in range(repeticiones):
        r = _una_corrida(raiz=raiz)
        h = _huellas(raiz)
        if estado["huellas"] is not None:
            estado["espurios"].append(sorted(k for k in h if h[k] != estado["huellas"].get(k)))
        estado["huellas"] = h
        estado["corridas"].append(r)
        print(f"  [{etiqueta}] corrida {i + 1}/{repeticiones}: {r['tiempo_s']:.2f} s · "
              f"RSS {r['pico_rss_mb']:.0f} MB · avisos {len(r['avisos'])}", flush=True)
        yield
    estado["perfiles"] = []
    for _ in range(N_PERFIL):   # corridas instrumentadas: se usa la mediana por etapa
        estado["perfiles"].append(_una_corrida(perfilar=True, raiz=raiz))
        yield
    yield estado


def _resultado(etiqueta: str, raiz: Path, estado: dict, modo: str) -> dict:
    corridas, perfiles, espurios = estado["corridas"], estado["perfiles"], estado["espurios"]
    tiempos = [c["tiempo_s"] for c in corridas]
    total_perfil = statistics.median(p["tiempo_s"] for p in perfiles)
    etapas = {e: round(statistics.median(sum(p["funciones"].get(n, 0.0) for n in nombres) for p in perfiles), 3)
              for e, nombres in ETAPAS.items()}
    etapas_pct = {e: round(100 * v / total_perfil, 1) for e, v in etapas.items()}
    perfil = perfiles[-1]
    avisos = corridas[-1]["avisos"]
    tipos = {}
    for cat, *_ in avisos:
        tipos[cat] = tipos.get(cat, 0) + 1
    unicos = sorted({f"{cat}: {msg} ({archivo}:{linea})" for cat, msg, archivo, linea in avisos})
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=raiz, capture_output=True,
                            text=True).stdout.strip()
    sucio = bool(subprocess.run(["git", "status", "--porcelain", "src"], cwd=raiz, capture_output=True,
                                text=True).stdout.strip())
    res = {
        "etiqueta": etiqueta,
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit + (" + cambios sin commit en src/" if sucio else ""),
        "modo": modo,
        "entorno": {"python": platform.python_version(), "so": platform.platform(), "cpu": platform.processor(),
                    "nucleos": __import__("os").cpu_count()},
        "repeticiones": len(corridas),
        "tiempo_s": {"mediana": round(statistics.median(tiempos), 3), "min": round(min(tiempos), 3),
                     "max": round(max(tiempos), 3), "todas": [round(t, 3) for t in tiempos]},
        "tiempo_por_etapa_s": etapas,
        "tiempo_por_etapa_pct": etapas_pct,
        "tiempo_instrumentado_s": round(total_perfil, 2),
        "memoria_mb": {"pico_rss_mediana": round(statistics.median(c["pico_rss_mb"] for c in corridas), 1),
                       "pico_python_mediana": round(statistics.median(p["pico_python_mb"] for p in perfiles), 1)},
        "corridas_instrumentadas": len(perfiles),
        "errores": {
            "avisos_total": len(avisos), "avisos_por_tipo": tipos, "avisos_distintos": unicos[:40],
            "archivos_que_cambian_sin_datos_nuevos": espurios[-1] if espurios else [],
            "n_archivos_que_cambian_sin_datos_nuevos": len(espurios[-1]) if espurios else 0,
            **_errores_de_datos(raiz),
        },
        "tamano_salidas_mb": _tamanos(raiz),
        "funciones_mas_lentas_s": dict(sorted(((k, round(v, 3)) for k, v in perfil["funciones"].items()
                                              if not k.startswith("<")), key=lambda x: -x[1])[:25]),
    }
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"benchmark_{etiqueta}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                                        encoding="utf-8")
    return res


def medir(etiqueta: str, repeticiones: int, raiz: Path = RAIZ) -> dict:
    gen = _corridas(raiz, repeticiones, etiqueta)
    estado = None
    for estado in gen:
        pass
    return _resultado(etiqueta, raiz, estado, "secuencial")


def medir_ab(ref: str, repeticiones: int) -> tuple[dict, dict]:
    """A/B intercalado: 'antes' = git worktree en `ref`; 'despues' = este directorio."""
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="bench_antes_"))
    wt = tmp / "repo"
    subprocess.run(["git", "worktree", "add", "--detach", str(wt), ref], cwd=RAIZ, check=True,
                   capture_output=True)
    try:
        ga, gd = _corridas(wt, repeticiones, "antes"), _corridas(RAIZ, repeticiones, "despues")
        ea = ed = None
        for _ in range(repeticiones + N_PERFIL + 1):   # alterna A, B, A, B, ... (limpias y luego perfiladas)
            ea = next(ga)
            ed = next(gd)
        antes = _resultado("antes", wt, ea, f"A/B intercalado contra {ref}")
        despues = _resultado("despues", RAIZ, ed, f"A/B intercalado contra {ref}")
        return antes, despues
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=RAIZ, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def comparar() -> dict:
    a = json.loads((DESTINO / "benchmark_antes.json").read_text(encoding="utf-8"))
    d = json.loads((DESTINO / "benchmark_despues.json").read_text(encoding="utf-8"))

    def fila(nombre, va, vd, unidad, menor_es_mejor=True):
        cambio = (vd - va) / va * 100 if va else (0.0 if vd == va else -100.0)
        return {"metrica": nombre, "antes": va, "despues": vd, "unidad": unidad,
                "cambio_pct": round(cambio, 1), "mejora": (vd < va) if menor_es_mejor else (vd > va)}

    filas = [
        fila("Tiempo total (mediana)", a["tiempo_s"]["mediana"], d["tiempo_s"]["mediana"], "s"),
        fila("Memoria pico del proceso (RSS)", a["memoria_mb"]["pico_rss_mediana"], d["memoria_mb"]["pico_rss_mediana"], "MB"),
        fila("Memoria pico de Python (tracemalloc)", a["memoria_mb"]["pico_python_mediana"],
             d["memoria_mb"]["pico_python_mediana"], "MB"),
        fila("Avisos durante la ejecución", a["errores"]["avisos_total"], d["errores"]["avisos_total"], "avisos"),
        fila("Registros inválidos generados por el pipeline", a["errores"]["registros_invalidos_generados_por_el_pipeline"],
             d["errores"]["registros_invalidos_generados_por_el_pipeline"], "registros"),
        fila("Errores detectados hasta la capa Oro", a["errores"]["errores_detectados_hasta_oro"],
             d["errores"]["errores_detectados_hasta_oro"], "registros"),
        fila("Archivos que cambian sin datos nuevos", a["errores"]["n_archivos_que_cambian_sin_datos_nuevos"],
             d["errores"]["n_archivos_que_cambian_sin_datos_nuevos"], "archivos"),
    ] + [fila(f"Tamaño en disco: {c}", a["tamano_salidas_mb"][c], d["tamano_salidas_mb"][c], "MB")
         for c in a["tamano_salidas_mb"]]
    etapas = [fila(f"Etapa: {e}", a["tiempo_por_etapa_s"][e], d["tiempo_por_etapa_s"].get(e, 0.0), "s (instrumentado)")
              for e in a["tiempo_por_etapa_s"]]
    out = {"antes": {"commit": a["commit"], "fecha": a["fecha_utc"]},
           "despues": {"commit": d["commit"], "fecha": d["fecha_utc"]},
           "entorno": d["entorno"], "repeticiones": d["repeticiones"], "metricas": filas, "etapas": etapas}
    (DESTINO / "comparativa.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    def tabla(fs):
        lineas = ["| Métrica | Antes | Después | Cambio |", "|---|---:|---:|---:|"]
        for f in fs:
            marca = "✅" if f["mejora"] else ("➖" if f["antes"] == f["despues"] else "⚠️")
            lineas.append(f"| {f['metrica']} ({f['unidad']}) | {f['antes']} | {f['despues']} | "
                          f"{f['cambio_pct']:+.1f} % {marca} |")
        return "\n".join(lineas)

    md = (f"# Comparativa antes vs. después\n\nAntes: commit `{a['commit']}` · Después: commit `{d['commit']}` · "
          f"{d['repeticiones']} repeticiones por versión, cada una en un proceso nuevo · "
          f"{d['entorno']['so']}, Python {d['entorno']['python']}\n\n## Métricas principales\n\n{tabla(filas)}\n\n"
          f"## Tiempo por etapa (mediana de {N_PERFIL} corridas instrumentadas con cProfile; los valores "
          f"absolutos están inflados por el perfilador y sirven para comparar entre versiones)\n\n"
          f"{tabla(etapas)}\n")
    (DESTINO / "comparativa.md").write_text(md, encoding="utf-8")
    print(md)
    return out


def graficar(destino_img: Path = RAIZ / "docs" / "E3" / "img" / "comparativa.png") -> Path:
    """Figura de la comparativa (tiempo, memoria, errores y etapas) para la documentación."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    c = json.loads((DESTINO / "comparativa.json").read_text(encoding="utf-8"))
    m = {f["metrica"]: f for f in c["metricas"]}
    gris, azul = "#b8c2cc", "#2f6fb5"
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.2), gridspec_kw={"width_ratios": [1, 1.4, 1.6, 2.4]})

    def barras(eje, nombres, etiquetas, titulo, unidad):
        a = [m[n]["antes"] for n in nombres]
        d = [m[n]["despues"] for n in nombres]
        x = range(len(nombres))
        eje.bar([i - .2 for i in x], a, .4, color=gris, label="Antes")
        eje.bar([i + .2 for i in x], d, .4, color=azul, label="Después")
        for i, n in enumerate(nombres):
            eje.text(i + .2, d[i], f"{m[n]['cambio_pct']:+.0f} %", ha="center", va="bottom", fontsize=9,
                     fontweight="bold", color=azul)
        eje.set_xticks(list(x), etiquetas, fontsize=9)
        eje.set_title(titulo, fontsize=11)
        eje.set_ylabel(unidad)
        eje.spines[["top", "right"]].set_visible(False)

    barras(ax[0], ["Tiempo total (mediana)"], ["Tiempo total"], "Tiempo de ejecución", "segundos")
    barras(ax[1], ["Memoria pico del proceso (RSS)", "Memoria pico de Python (tracemalloc)"],
           ["Proceso (RSS)", "Python"], "Memoria pico", "MB")
    barras(ax[2], ["Registros inválidos generados por el pipeline", "Errores detectados hasta la capa Oro",
                   "Archivos que cambian sin datos nuevos"], ["Imputaciones\ninválidas", "Errores\nhasta Oro",
                                                              "Archivos que\ncambian solos"],
           "Errores", "conteo")
    et = c["etapas"]
    nombres = [e["metrica"].replace("Etapa: ", "") for e in et]
    y = range(len(et))
    ax[3].barh([i + .2 for i in y], [e["antes"] for e in et], .4, color=gris, label="Antes")
    ax[3].barh([i - .2 for i in y], [e["despues"] for e in et], .4, color=azul, label="Después")
    ax[3].set_yticks(list(y), nombres, fontsize=9)
    ax[3].invert_yaxis()
    ax[3].set_title("Tiempo por etapa (instrumentado)", fontsize=11)
    ax[3].set_xlabel("segundos (con perfilador)")
    ax[3].spines[["top", "right"]].set_visible(False)
    ax[3].legend(frameon=False, fontsize=9)
    fig.suptitle(f"Optimización del pipeline · {c['repeticiones']} corridas intercaladas por versión "
                 f"(antes {c['antes']['commit']} · después {c['despues']['commit'].split()[0]})", fontsize=12)
    fig.tight_layout()
    destino_img.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino_img, dpi=140)
    return destino_img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--etiqueta", default="despues")
    ap.add_argument("--repeticiones", type=int, default=5)
    ap.add_argument("--comparar", action="store_true")
    ap.add_argument("--ab", metavar="REF", help="commit o tag de la versión 'antes' para el A/B intercalado")
    args = ap.parse_args()
    if args.comparar:
        comparar()
        graficar()
    elif args.ab:
        medir_ab(args.ab, args.repeticiones)
        comparar()
        graficar()
    else:
        r = medir(args.etiqueta, args.repeticiones)
        print(json.dumps({k: r[k] for k in ["tiempo_s", "memoria_mb", "tiempo_por_etapa_s", "tamano_salidas_mb"]},
                         indent=2, ensure_ascii=False))
        print(json.dumps({k: v for k, v in r["errores"].items() if k != "avisos_distintos"}, indent=2,
                         ensure_ascii=False))
