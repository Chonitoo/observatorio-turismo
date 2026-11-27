# Relatoría de etapa — E3: más rápido, más ligero, sin errores, y listo para compartir

**Observatorio de Ocupación Hotelera de Colima** · Maximiliano Encarnación Velázquez Rodríguez · noviembre 2026

---

## 1. Punto de partida

Al cerrar E2 el pipeline funcionaba de punta a punta: capturaba cuatro fuentes, limpiaba, validaba, integraba,
procesaba el mapa y rastreaba cada dato. Pero nunca se había medido **cuánto tardaba**, **cuánta memoria usaba** ni
**cuántos errores producía él mismo**. Además, los datos sólo vivían dentro del proyecto: un tercero no tenía forma
sencilla de usarlos ni de saber qué contenían.

## 2. Qué se hizo

1. **Instrumento de medición.** `src/benchmark.py` mide tiempo, memoria (del proceso y de Python), avisos, errores
   de datos y no determinismo. Cada corrida usa un proceso nuevo.
2. **Línea base y perfilado.** Se midió la versión de E2 (commit `d8ba5e4`) y se usó `cProfile` para encontrar los
   cuellos de botella: escritura de CSV (20 % del tiempo), lectura de Bronce, cálculo de huecos fila por fila y el
   Isolation Forest. Con `tracemalloc` se vio que los picos de memoria venían de cargar completo el CSV del DENUE
   (22 MB descomprimidos), dos veces.
3. **Optimización** en tres frentes (detalle en `docs/E3/ENTREGA.md`):
   - **Tiempo:** escritura con PyArrow, lectura con el motor PyArrow, código vectorizado y menos árboles en el
     Isolation Forest.
   - **Memoria:** lectura del DENUE como flujo y sólo con las columnas necesarias; verificación del linaje sin
     volver a parsear.
   - **Errores:** regla R6 en la entrada, imputaciones validadas antes de emitirse, sin imputación en pandemia,
     archivos deterministas y escritura atómica.
4. **Medición A/B intercalada.** La versión anterior y la nueva se corrieron alternadas, 7 veces cada una, en las
   mismas condiciones.
5. **Publicación del dataset** en `dataset/`:
   - 5 tablas curadas en CSV y Parquet, con diccionario de datos.
   - `datapackage.json` estándar, validado con Frictionless.
   - Licencia CC BY 4.0 con atribuciones y sumas SHA-256.
6. **Datasheet** siguiendo el marco *Datasheets for Datasets*.

## 3. Resultados

| | Antes | Después |
|---|---:|---:|
| Tiempo (mediana) | 14.2 s | 9.6 s (**−32 %**) |
| Memoria del proceso | 352 MB | 313 MB (**−11 %**) |
| Memoria de Python | 245 MB | 171 MB (**−30 %**) |
| Imputaciones inválidas | 1 | **0** |
| Errores que llegaban hasta Oro | 2 | **0** |
| Archivos que cambiaban sin datos nuevos | 2 | **0** |

## 4. Decisiones difíciles

**¿Cómo medir de forma justa?** Las primeras mediciones daban entre 50 y 100 segundos, cuando el pipeline tardaba
unos 6. La causa era que el perfilador y `tracemalloc` agregan muchísima sobrecarga. Se separaron las corridas
*limpias* (para tiempo y memoria) de las *instrumentadas* (sólo para el desglose por etapa). Aun así, el tiempo
variaba de 5 a 13 segundos según lo que hiciera la computadora en ese momento. Comparar "antes" medido el lunes contra
"después" medido el martes no sería honesto, así que se programó el modo **A/B intercalado** con un *git worktree*
de la versión anterior.

**Optimizar sin cambiar los resultados.** Un pipeline más rápido no sirve si da otros números. Después de cada
optimización de rendimiento se compararon las salidas con las anteriores y quedaron **idénticas byte por byte**. Las
únicas diferencias en los datos vienen de las correcciones de errores, que se hicieron a propósito y quedaron
documentadas.

**¿Qué cuenta como "error"?** El pipeline no fallaba ni mostraba avisos, así que a primera vista no tenía errores.
Al buscar con más cuidado aparecieron tres tipos:
1. Un registro que **el propio pipeline inventaba mal**: una imputación con cuartos ocupados y cero turistas.
2. Errores que se detectaban **demasiado tarde**: estadías de 50 noches que sólo se veían al agregar en Oro.
3. Archivos que **cambiaban en cada corrida** sin que cambiaran los datos, y generaban commits falsos cada semana.

**No imputar durante la pandemia.** Al revisar el caso de Nuevo Nayarit se vio que, si se borraba ese registro y se
rellenaba el hueco con los meses vecinos, el pipeline habría "inventado" ocupación normal en pleno cierre de hoteles
(abril de 2020). La regla correcta fue no imputar huecos en meses de choque, aunque eso signifique 21 imputaciones
menos.

**Un error encontrado al medir.** Durante el benchmark, Windows bloqueó un archivo de salida y el pipeline se cayó a
la mitad. En GitHub Actions nunca había pasado, pero en una computadora real sí puede pasar. Se agregó escritura
atómica con reintentos.

## 5. Problemas encontrados

| Problema | Solución |
|---|---|
| El perfilador inflaba los tiempos 5-10 veces | Corridas limpias para medir y corridas instrumentadas sólo para el desglose |
| Mucho ruido en los tiempos de la máquina | Medición A/B intercalada con medianas |
| El escritor de PyArrow entrecomillaba todos los textos (archivos 6 % más grandes) | Sin comillas cuando es posible y pandas cuando un valor trae comas; se quitaron comas de nuestras propias etiquetas |
| `RuntimeWarning: Mean of empty slice` al calcular la mediana de una serie vacía | Se protege el caso vacío; el pipeline corre sin avisos incluso con `-W error` |
| El `datapackage.json` no pasaba la validación de Frictionless | Faltaba declarar cada tabla como `tabular-data-resource` |
| Git podía cambiar los saltos de línea y romper las sumas SHA-256 publicadas | `dataset/** -text` en `.gitattributes` |

## 6. Aprendizajes

> ✏️ *Sección para que el autor la redacte con su propia reflexión. Ideas de partida:*

- `[Por qué hay que medir antes de optimizar, y qué me sorprendió de dónde se iba el tiempo]`
- `[La diferencia entre que un programa "no falle" y que "no tenga errores"]`
- `[Por qué una optimización tiene que demostrar que no cambió los resultados]`
- `[Qué necesita un dataset para que otra persona lo pueda usar con confianza (licencia, diccionario, datasheet)]`

## 7. Indicadores del proceso (PSP)

| Indicador | Meta | Resultado E3 |
|---|---|---|
| Q1 · Corridas de Actions en verde | ≥ 95 % | `[completar al cerrar]` |
| Q2 · Trazabilidad completa | 100 % | 100 %: linaje íntegro y dataset con `id_registro` rastreable |
| Q3a · Defectos que llegan a `main` | ≤ 10 / KLOC | 1 (un cambio al benchmark quedó fuera de un commit y se completó en el siguiente); 8 registrados en total |

## 8. Siguientes pasos

1. Pronóstico de la ocupación de Manzanillo con el dataset publicado (SARIMA/SARIMAX).
2. Archivar la versión `e3` del dataset en Zenodo para obtener un DOI.
3. Agregar una variable de Semana Santa y puentes para reducir los atípicos sin explicación.
