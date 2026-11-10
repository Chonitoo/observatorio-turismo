# Sistema de calidad (PSP)

Registro personal según el *Personal Software Process* (Humphrey). Integrante: **Maximiliano Encarnación Velázquez Rodríguez**.

| Archivo | Contenido |
|---|---|
| `tiempo-maximiliano.csv` | Bitácora de tiempo: fecha, inicio, fin, interrupciones, minutos netos (`delta_min`), fase y actividad. |
| `defectos-maximiliano.csv` | Bitácora de defectos: tipo según el estándar PSP, fase en que se inyectó y en que se removió, y minutos de corrección. |

**Fases:** `PLAN` planeación · `DLD` diseño · `CODE` codificación · `REV` revisión · `TEST` pruebas · `DOC` documentación · `PM` postmortem.

**Tipos de defecto (estándar PSP):** 10 Documentación · 20 Sintaxis · 30 Construcción/paquetes · 40 Asignación · 50 Interfaz · 60 Verificación · 70 Datos · 80 Función · 90 Sistema · 100 Entorno.

## Objetivos de calidad medibles

| # | Objetivo | Métrica y fórmula | Meta | Cómo se mide |
|---|---|---|---|---|
| **Q1** | **Confiabilidad de la captura** | % de corridas programadas de GitHub Actions que terminan en verde = corridas exitosas / corridas programadas × 100 | **≥ 95 %** por entrega | Historial de la pestaña *Actions* y la bitácora `data/bronze/_bitacora_captura.csv`. |
| **Q2** | **Integridad y trazabilidad de Bronce** | % de archivos crudos con registro completo en la bitácora (URL, HTTP, bytes, SHA-256) y hash verificado | **100 %** | La prueba `tests/test_bronce.py` corre en cada ejecución; cualquier falla bloquea la captura. |
| **Q3** | **Calidad del proceso personal** | (a) Densidad de defectos que llegan a la rama `main` = defectos encontrados después del commit / KLOC · (b) Error de estimación de tiempo = \|real − estimado\| / estimado | (a) **≤ 10 defectos/KLOC** · (b) **≤ 25 %** | Bitácoras de tiempo y defectos; se revisa en el postmortem de cada entrega. |

**Estimación para E0:** 240 min. El tiempo real se registra en `tiempo-maximiliano.csv` y se compara en el postmortem.
