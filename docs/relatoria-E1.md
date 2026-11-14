# Relatoría de etapa — E1: de datos crudos a datos confiables

**Observatorio de Ocupación Hotelera de Colima** · Maximiliano Encarnación Velázquez Rodríguez · noviembre 2026

---

## 1. Punto de partida

Al cerrar E0 el observatorio tenía una capa Bronce con tres fuentes crudas: la ocupación hotelera de 64 destinos
de DataTur (31,147 registros, 2016–2024) y dos series de Banxico (tipo de cambio FIX diario e INPC mensual),
capturadas por un extractor automático en GitHub Actions. Esos datos todavía no eran confiables para analizar:
venían en formatos distintos, con huecos y con algunos registros que, a simple vista, eran imposibles.

El objetivo de E1 fue construir el camino automático **Bronce → Plata → Oro**, que limpia, valida e integra los
datos sin borrar nada en silencio.

## 2. Qué se hizo

1. **Perfilado de los datos crudos.** Antes de escribir reglas se exploró el archivo para saber qué problemas
   existían de verdad: 1 valor nulo, 2 registros con más cuartos ocupados que disponibles, 4 con cuartos ocupados
   pero cero llegadas y 2,447 combinaciones destino × categoría × mes ausentes.
2. **Puerta de Calidad con Pandera.** Se definieron esquemas para las tres etapas (entrada, Plata y Oro) con reglas
   de tipo, dominio, rango y consistencia lógica (R1–R5, O1). Los registros que fallan van a `data/quarantine/` con
   su motivo, y en cada puerta se verifica que *válidos + cuarentena = entrada*.
3. **Diagnóstico de faltantes.** Con pruebas ji-cuadrada se demostró que la ausencia **no es MCAR**: depende de la
   categoría, del año y del tipo de destino. Se separaron los huecos internos cortos (MAR, 147 imputados) de los
   huecos estructurales (MNAR, 2,300 sin imputar).
4. **Integración.** Se resolvieron conflictos de formato (CSV contra JSON), de llave temporal (`anio`+`mes` contra
   `dd/mm/aaaa`), de tipo (texto a número), de frecuencia (diaria a mensual), de granularidad y de unidades
   (INPC a inflación anual).
5. **Atípicos y ruido.** Cada serie se descompuso en tendencia, estacionalidad y residuo. Sobre el residuo se
   aplicaron IQR y Z-Score robusto, con Isolation Forest como contraste multivariado.
6. **Transformaciones.** Se agregaron jerarquías (tiempo, espacio, producto), discretizaciones, normalización
   Min-Max y Z-Score, y la reducción por agregación y selección.
7. **Automatización y pruebas.** El pipeline corre en GitHub Actions después de cada captura; 9 pruebas nuevas (14 en total)
   verifican la puerta, la imputación, los atípicos y las transformaciones.

## 3. Decisiones difíciles y por qué se tomaron

**¿Imputar o no imputar los huecos?** La tentación era rellenar todos los meses faltantes. Al revisar los huecos
se vio que muchos son categorías que simplemente no existían en ese destino: por ejemplo, Colima no tiene hoteles
5★ reportados en 91 de 108 meses. Imputarlos habría inventado cuartos de hotel y habría inflado la oferta. Por
eso sólo se imputan huecos internos de hasta 3 meses dentro de una serie activa.

**¿La pandemia es un atípico?** Estadísticamente sí: Manzanillo cayó a 1.5 % de ocupación en abril de 2020. Pero
no es un error, es lo que pasó. "Corregirlo" borraría la información más importante para entender la
recuperación. Se decidió conservar esos valores y marcarlos, igual que el huracán Otis en Acapulco.

**El primer intento de atípicos marcaba demasiado.** La primera versión comparaba cada mes contra la mediana de
ese mismo mes y marcaba como atípicos enero y febrero de 2020. La causa era que el crecimiento de los destinos y
la caída de la pandemia distorsionaban la referencia. Se agregó la tendencia, estimada sin los meses de choque, y
el porcentaje corregido bajó a 2.5 %.

**Nulos legítimos.** La puerta de Oro rechazaba los meses de cierre total por COVID porque la estadía promedio
salía nula (0 llegadas / 0 noches). Ese nulo no es un error, es una división indefinida. Se permitió el nulo sólo
cuando las llegadas son cero (regla O1), y la regla sigue atrapando cualquier otro nulo.

## 4. Problemas encontrados y cómo se resolvieron

| Problema | Solución |
|---|---|
| Los motivos de cuarentena se repetían una vez por cada columna del registro | Las reglas de registro se reportan una sola vez |
| Un registro imputado violaba la regla R2 | La Puerta 2 lo detectó y lo mandó a cuarentena: la validación también audita la imputación |
| La inflación de 2016 salía nula | El extractor de Banxico se amplió a 2015 y la corrida automática #2 completó el dato |
| scikit-learn fue bloqueado por el control de aplicaciones de Windows en la primera instalación | Isolation Forest quedó opcional; IQR y Z robusto no dependen de esa librería |
| Estadías de 44 y 53 noches en Nuevo Nayarit (2020) | Quedaron en cuarentena: con sólo 17–20 llegadas en el mes, la razón noches/llegadas pierde sentido |

## 5. Hallazgos sobre el sector

- La ausencia de datos crece después de 2020 en los segmentos económicos: las series de 1★ pasan de 11 % a 21 % de
  meses faltantes y las de 2★ de 4 % a 11 %, mientras que 3★ y 4★ casi no cambian. Esto es compatible con el
  cierre o la salida del monitoreo de establecimientos pequeños después de la pandemia (hipótesis por verificar).
- Al pasar a niveles, Manzanillo nunca alcanza ocupación "Alta" (≥ 60 %) en temporada baja o media; en temporada
  alta lo logra en una fracción de los meses. Esto confirma lo dicho en la entrevista de campo sobre la fuerte
  dependencia de las vacaciones.
- Algunos atípicos "sin explicación" coinciden con **Semana Santa**, que cambia entre marzo y abril. El
  entrevistado mencionó los puentes y las vacaciones como factores clave, y los datos lo respaldan.

## 6. Aprendizajes

En esta segunda entrega analicé los conjuntos de datos y encontré problemas y discrepancias que no esperaba:
2 registros con más cuartos ocupados que cuartos disponibles en el hotel, 4 registros con cuartos ocupados pero
cero turistas y más de 2,400 meses que simplemente no aparecían en el archivo.

**La Puerta de Calidad.** Para manejar esos problemas implementamos una puerta de seguridad con Pandera, que revisa
cada registro contra un conjunto de reglas. Los datos que no cumplen los requisitos no se borran: se mandan a una
carpeta de cuarentena con la descripción del motivo.

**Los datos faltantes.** Al principio no sabía por qué faltaban datos y creía que había que rellenarlos todos para
no dejar huecos en la estadística. Investigando entendí que primero hay que analizar estadísticamente *por qué*
faltan, y que de ese análisis depende la decisión correcta: rellenar sólo los huecos que se pueden explicar con la
información que sí existe y dejar sin rellenar los que no, para que la hipótesis que se construya sea correcta, o lo
más cercana posible a la realidad.

**La automatización.** Me sorprende cómo el sistema corrige y monitorea los datos por sí solo: filtra y separa
automáticamente los registros escasos o incoherentes y los manda a cuarentena. Así no se pierden; simplemente quedan
en un estado inactivo, documentados y disponibles para revisarse.

## 7. Indicadores del proceso (PSP)

| Indicador | Meta | Resultado E1 |
|---|---|---|
| Q1 · Corridas de Actions en verde | ≥ 95 % | 100 % (2 de 2 corridas en verde al cierre de E1) |
| Q2 · Archivos con trazabilidad completa | 100 % | 100 %: cada salida de Plata y Oro se regenera desde Bronce con reporte en `reports/E1/` |
| Q3a · Defectos que llegan a `main` | ≤ 10 / KLOC | 0 defectos conocidos en `main` sobre ~1.06 KLOC; 6 defectos registrados y corregidos antes del commit |
| Q3b · Error de estimación de tiempo | ≤ 25 % | `[completar con la bitácora de tiempo]` |

## 8. Siguientes pasos (E2 y pronóstico)

1. Agregar una variable indicadora de Semana Santa y de puentes oficiales.
2. Usar `data/gold/hotel_categoria_mes.csv` para el diseño factorial (tipo de destino × categoría × temporada ×
   periodo).
3. Usar `data/gold/serie_colima.csv` para los modelos de pronóstico (SARIMA y SARIMAX con tipo de cambio y la
   variable `choque_covid`).
4. Buscar una actualización de DataTur con datos de 2025.
