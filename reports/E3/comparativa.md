# Comparativa antes vs. después

Antes: commit `d8ba5e4` · Después: commit `230bea0` · 7 repeticiones por versión, cada una en un proceso nuevo · Windows-11-10.0.26200-SP0, Python 3.12.10

## Métricas principales

| Métrica | Antes | Después | Cambio |
|---|---:|---:|---:|
| Tiempo total (mediana) (s) | 14.24 | 9.608 | -32.5 % ✅ |
| Memoria pico del proceso (RSS) (MB) | 352.4 | 313.3 | -11.1 % ✅ |
| Memoria pico de Python (tracemalloc) (MB) | 244.6 | 171.1 | -30.0 % ✅ |
| Avisos durante la ejecución (avisos) | 0 | 0 | +0.0 % ➖ |
| Registros inválidos generados por el pipeline (registros) | 1 | 0 | -100.0 % ✅ |
| Errores detectados hasta la capa Oro (registros) | 2 | 0 | -100.0 % ✅ |
| Archivos que cambian sin datos nuevos (archivos) | 2 | 0 | -100.0 % ✅ |
| Tamaño en disco: data/silver (MB) | 9.78 | 9.33 | -4.6 % ✅ |
| Tamaño en disco: data/gold (MB) | 22.12 | 21.9 | -1.0 % ✅ |
| Tamaño en disco: data/quarantine (MB) | 0.01 | 0.0 | -100.0 % ✅ |

## Tiempo por etapa (mediana de 3 corridas instrumentadas con cProfile; los valores absolutos están inflados por el perfilador y sirven para comparar entre versiones)

| Métrica | Antes | Después | Cambio |
|---|---:|---:|---:|
| Etapa: lectura_bronce (s (instrumentado)) | 6.084 | 1.778 | -70.8 % ✅ |
| Etapa: puertas_calidad (s (instrumentado)) | 3.815 | 2.895 | -24.1 % ✅ |
| Etapa: faltantes (s (instrumentado)) | 8.228 | 4.235 | -48.5 % ✅ |
| Etapa: integracion (s (instrumentado)) | 3.69 | 3.44 | -6.8 % ✅ |
| Etapa: atipicos (s (instrumentado)) | 13.063 | 8.621 | -34.0 % ✅ |
| Etapa: transformacion (s (instrumentado)) | 1.239 | 1.262 | +1.9 % ⚠️ |
| Etapa: geoespacial (s (instrumentado)) | 0.281 | 0.255 | -9.3 % ✅ |
| Etapa: linaje (s (instrumentado)) | 2.411 | 1.149 | -52.3 % ✅ |
| Etapa: escritura (s (instrumentado)) | 9.251 | 0.152 | -98.4 % ✅ |
