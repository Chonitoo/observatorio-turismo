"""Orquestador de la máquina de captura (capa Bronce).

Uso:  python -m src.captura

Ejecuta todos los extractores, imprime un resumen y termina con código 1 sólo si
NINGUNA fuente pudo capturarse (para que GitHub Actions marque la corrida en rojo).
Un bloqueo de una fuente individual se registra en la bitácora pero no detiene a las demás.
"""
import sys

from src.extractores import banxico, datatur

ESTADOS_OK = {"nuevo", "sin_cambios"}


def main() -> int:
    resultados = [datatur.capturar(), *banxico.capturar()]
    print(f"{'fuente':<24}{'estado':<14}{'http':<6}{'bytes':>10}  archivo / nota")
    for r in resultados:
        print(f"{r.fuente:<24}{r.estado:<14}{str(r.http or ''):<6}{r.bytes:>10}  {r.archivo or r.nota}")
    exitosas = sum(r.estado in ESTADOS_OK for r in resultados)
    print(f"\n{exitosas}/{len(resultados)} capturas exitosas")
    return 0 if exitosas else 1


if __name__ == "__main__":
    sys.exit(main())
