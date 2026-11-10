"""Utilidades compartidas de la máquina de captura (capa Bronce).

Principios de la capa Bronce:
  * El dato crudo se guarda TAL CUAL llega de la fuente (sin limpiar ni transformar).
  * Cada archivo es inmutable: el nombre lleva la fecha de captura y nunca se sobrescribe.
  * Toda captura (exitosa o fallida) queda registrada en data/bronze/_bitacora_captura.csv
    con URL, código HTTP, tamaño y huella SHA-256 para garantizar trazabilidad.
  * Si el contenido no cambió respecto a la última captura (mismo SHA-256), no se duplica.

Principios éticos:
  * Se consulta robots.txt antes de descargar (RFC 9309) y se respeta Crawl-delay.
  * El cliente se identifica honestamente con un User-Agent propio y un enlace al proyecto.
  * Una sola petición por recurso y por ejecución; sin paralelismo ni reintentos agresivos.
"""
from __future__ import annotations

import csv
import hashlib
import time
import urllib.robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

RAIZ = Path(__file__).resolve().parents[1]
BRONCE = RAIZ / "data" / "bronze"
BITACORA = BRONCE / "_bitacora_captura.csv"

USER_AGENT = (
    "ObservatorioTurismoColima/0.1 "
    "(proyecto academico; +https://github.com/Chonitoo/observatorio-turismo)"
)
TIMEOUT = 60
CAMPOS_BITACORA = [
    "fecha_utc", "fuente", "url", "robots", "http", "estado",
    "bytes", "sha256", "archivo", "nota",
]


@dataclass
class ResultadoCaptura:
    fuente: str
    url: str
    robots: str
    http: int | None
    estado: str  # nuevo | sin_cambios | bloqueado | error | no_permitido
    bytes: int = 0
    sha256: str = ""
    archivo: str = ""
    nota: str = ""


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def revisar_robots(url: str) -> tuple[bool, str, float]:
    """Devuelve (permitido, descripcion, crawl_delay).

    Según RFC 9309: si robots.txt responde 4xx se considera "no disponible" y el
    acceso está permitido; si responde 5xx o hay error de red se asume prohibido.
    """
    p = urlparse(url)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        r = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    except requests.RequestException as e:
        return False, f"robots inaccesible ({type(e).__name__}); se asume prohibido", 0.0
    if 400 <= r.status_code < 500:
        return True, f"robots.txt HTTP {r.status_code} (no disponible => permitido, RFC 9309)", 0.0
    if r.status_code >= 500:
        return False, f"robots.txt HTTP {r.status_code} => se asume prohibido", 0.0
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r.text.splitlines())
    permitido = rp.can_fetch(USER_AGENT, url)
    delay = float(rp.crawl_delay(USER_AGENT) or 0)
    return permitido, f"robots.txt {'permite' if permitido else 'PROHÍBE'} la ruta", delay


def ultimo_sha(fuente: str) -> str:
    if not BITACORA.exists():
        return ""
    with BITACORA.open(encoding="utf-8", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r["fuente"] == fuente and r["sha256"]]
    return filas[-1]["sha256"] if filas else ""


def registrar(res: ResultadoCaptura) -> None:
    BRONCE.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with BITACORA.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_BITACORA)
        if nuevo:
            w.writeheader()
        w.writerow({
            "fecha_utc": ahora_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fuente": res.fuente, "url": res.url, "robots": res.robots,
            "http": res.http if res.http is not None else "", "estado": res.estado,
            "bytes": res.bytes, "sha256": res.sha256, "archivo": res.archivo, "nota": res.nota,
        })


def descargar_crudo(
    fuente: str,
    url: str,
    nombre_base: str,
    extension: str,
    headers: dict | None = None,
    url_para_bitacora: str | None = None,
) -> ResultadoCaptura:
    """Descarga un recurso respetando robots.txt y lo guarda sin modificar en Bronce."""
    url_log = url_para_bitacora or url
    permitido, desc_robots, delay = revisar_robots(url)
    if not permitido:
        res = ResultadoCaptura(fuente, url_log, desc_robots, None, "no_permitido")
        registrar(res)
        return res
    if delay:
        time.sleep(delay)

    h = {"User-Agent": USER_AGENT}
    h.update(headers or {})
    try:
        r = requests.get(url, headers=h, timeout=TIMEOUT)
    except requests.RequestException as e:
        res = ResultadoCaptura(fuente, url_log, desc_robots, None, "error", nota=type(e).__name__)
        registrar(res)
        return res

    if r.status_code in (401, 403, 429):
        # No se intenta evadir el bloqueo (sin cambiar User-Agent, IP ni reintentos).
        res = ResultadoCaptura(fuente, url_log, desc_robots, r.status_code, "bloqueado",
                               nota="El servidor rechazó la petición; no se intenta evadir.")
        registrar(res)
        return res
    if r.status_code != 200:
        res = ResultadoCaptura(fuente, url_log, desc_robots, r.status_code, "error")
        registrar(res)
        return res

    contenido = r.content
    sha = hashlib.sha256(contenido).hexdigest()
    if sha == ultimo_sha(fuente):
        res = ResultadoCaptura(fuente, url_log, desc_robots, 200, "sin_cambios",
                               len(contenido), sha, nota="Contenido idéntico a la última captura")
        registrar(res)
        return res

    destino_dir = BRONCE / fuente
    destino_dir.mkdir(parents=True, exist_ok=True)
    sello = ahora_utc().strftime("%Y-%m-%dT%H%M%SZ")
    destino = destino_dir / f"{nombre_base}_{sello}.{extension}"
    destino.write_bytes(contenido)
    res = ResultadoCaptura(fuente, url_log, desc_robots, 200, "nuevo", len(contenido), sha,
                           destino.relative_to(RAIZ).as_posix())
    registrar(res)
    return res
