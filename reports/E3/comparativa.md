# Comparativa antes vs. después

Antes: commit `d8ba5e4` · Después: commit `cd68304` · 7 repeticiones por versión, cada una en un proceso nuevo · Windows-11-10.0.26200-SP0, Python 3.12.10

## Métricas principales

| Métrica | Antes | Después | Cambio |
|---|---:|---:|---:|
| Tiempo total (mediana) (s) | 11.984 | 7.164 | -40.2 % ✅ |
| Memoria pico del proceso (RSS) (MB) | 352.1 | 315.1 | -10.5 % ✅ |
| Memoria pico de Python (tracemalloc) (MB) | 244.6 | 171.1 | -30.0 % ✅ |
| Avisos durante la ejecución (avisos) | 0 | 0 | +0.0 % ➖ |
| Registros inválidos generados por el pipeline (registros) | 1 | 0 | -100.0 % ✅ |
| Errores detectados hasta la capa Oro (registros) | 2 | 0 | -100.0 % ✅ |
| Archivos que cambian sin datos nuevos (archivos) | 2 | 0 | -100.0 % ✅ |
| Tamaño en disco: data/silver (MB) | 9.78 | 9.85 | +0.7 % ⚠️ |
| Tamaño en disco: data/gold (MB) | 22.12 | 23.55 | +6.5 % ⚠️ |
| Tamaño en disco: data/quarantine (MB) | 0.01 | 0.0 | -100.0 % ✅ |

## Tiempo por etapa (mediana, tiempo acumulado de cProfile)

| Métrica | Antes | Después | Cambio |
|---|---:|---:|---:|
| Etapa: lectura_bronce (s (instrumentado)) | 8.981 | 3.275 | -63.5 % ✅ |
| Etapa: puertas_calidad (s (instrumentado)) | 5.484 | 4.402 | -19.7 % ✅ |
| Etapa: faltantes (s (instrumentado)) | 11.919 | 4.186 | -64.9 % ✅ |
| Etapa: integracion (s (instrumentado)) | 2.743 | 5.656 | +106.2 % ⚠️ |
| Etapa: atipicos (s (instrumentado)) | 10.767 | 17.643 | +63.9 % ⚠️ |
| Etapa: transformacion (s (instrumentado)) | 1.752 | 2.557 | +45.9 % ⚠️ |
| Etapa: geoespacial (s (instrumentado)) | 0.411 | 0.468 | +13.9 % ⚠️ |
| Etapa: linaje (s (instrumentado)) | 3.836 | 2.142 | -44.2 % ✅ |
| Etapa: escritura (s (instrumentado)) | 10.433 | 0.22 | -97.9 % ✅ |
