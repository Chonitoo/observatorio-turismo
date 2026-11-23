# Relatoría de etapa — E2: ¿dónde está la oferta y de dónde viene cada dato?

**Observatorio de Ocupación Hotelera de Colima** · Maximiliano Encarnación Velázquez Rodríguez · noviembre 2026

---

## 1. Punto de partida

Al cerrar E1 el observatorio tenía un pipeline automático Bronce → Plata → Oro con DataTur y Banxico. Sabíamos
**cuánto** se ocupan los hoteles de Manzanillo, pero no **dónde** está la oferta de hospedaje ni cuánta queda fuera
de DataTur. Tampoco podíamos demostrar, registro por registro, de qué dato crudo salía cada número de la capa Oro.

## 2. Qué se hizo

1. **Búsqueda de la fuente geoespacial.** Se evaluaron OpenStreetMap (Overpass) y el DENUE del INEGI.
2. **Integración de DENUE y del Marco Geoestadístico** con el mismo extractor ético de E0: 294 establecimientos de
   hospedaje de Colima con coordenadas y 10 polígonos municipales con población.
3. **Minimización de datos personales.** Se descartaron 15 columnas (nombre, razón social, teléfono, correo,
   domicilio) antes de que los datos salieran de Bronce.
4. **Procesamiento con GeoPandas:** Puerta de Calidad geoespacial, unión espacial punto → municipio, densidades y
   mapas (estático e interactivo).
5. **Linaje completo:** cada registro lleva su origen desde Bronce, y la tabla `linaje_oro.csv` conecta los 7,310
   registros de Oro con sus 34,505 registros crudos. Una verificación automática detiene el pipeline si algo no cuadra.
6. **Declaración de ética** consolidada para las cinco fuentes.

## 3. Decisiones difíciles

**Descartar OpenStreetMap.** Overpass era la opción más rápida y no pedía registro. Al revisar su `robots.txt` vimos
que prohíbe `/api/` a cualquier agente, y OpenStreetMap pide no hacer *scraping*. Nuestro extractor está diseñado
para respetar robots.txt, así que usar Overpass habría contradicho los principios de E0. Se eligió DENUE, que además
es la fuente oficial del gobierno para unidades económicas.

**Qué hacer con los datos de contacto de DENUE.** La descarga trae nombre, teléfono y correo de cada negocio. Son
públicos, pero en una pensión o casa de huéspedes el "nombre del negocio" puede ser el de su dueño. Como el análisis
sólo necesita tipo, tamaño y ubicación, se decidió no conservarlos, y una prueba automática verifica que nunca
lleguen a Plata u Oro.

**Linaje sin hacer archivos gigantes.** Rastrear cada destino-mes día por día contra el tipo de cambio producía
~150 mil filas (38 MB). Como Banxico es un indicador nacional, se rastrea una sola vez por mes (`banxico|AAAA-MM`) y
cada destino-mes apunta a él. La trazabilidad es la misma y el archivo pesa 8.5 MB.

**Linaje de los datos imputados.** Un registro imputado no tiene fila en Bronce. En lugar de dejarlo "huérfano", se
documenta con los dos registros reales de los que se interpoló (`base_imputacion`), y el linaje los apunta.

## 4. Problemas encontrados

| Problema | Solución |
|---|---|
| robots.txt de Overpass prohíbe la API | Cambio de fuente a DENUE (INEGI) |
| El servidor del INEGI etiqueta el ZIP de DENUE como `text/html` | Se valida por contenido (firma `PK` y huella SHA-256), no por el encabezado |
| DENUE viene en latin-1 y las demás fuentes en UTF-8 | La codificación se declara al leer Bronce |
| El polígono costero es generalizado y algunos hoteles de playa "caen al mar" | Unión al municipio más cercano con tolerancia de 1 km (regla G-R2) |
| Un establecimiento declara Villa de Álvarez pero está en Colima | Se marca `municipio_coincide = False` y se usa el municipio espacial |
| GeoPandas no aceptaba tamaños de marcador como Serie en el mapa | Se pasaron como arreglo |

## 5. Hallazgos sobre el sector

- **Manzanillo concentra casi la mitad de la oferta de hospedaje del estado (46 %)** y los únicos 4 establecimientos
  grandes. Sus hoteles promedian ≈ 32 cuartos, contra ≈ 22 en Colima capital.
- **Armería** tiene la mayor densidad de hospedaje por habitante, por sus playas (Cuyutlán, El Paraíso), aunque no
  aparece en DataTur.
- **73 % de los establecimientos son micronegocios.** DENUE registra 26 departamentos o casas amuebladas y 24
  cabañas: oferta que DataTur no mide y que confirma lo que dijo el entrevistado sobre la renta vacacional.

## 6. Aprendizajes

**La fuente geoespacial.** En esta etapa agregamos una fuente de mapas: usamos el DENUE del INEGI para localizar
los 294 hoteles, moteles, cabañas y demás establecimientos de hospedaje de Colima, y determinar de cada uno su
ubicación, tamaño y municipio. Los límites municipales los obtuvimos del Marco Geoestadístico del INEGI y los
procesamos con la herramienta GeoPandas.

**Lo que mostró el mapa.** El mapa mostró que Manzanillo tiene casi la mitad de todo el hospedaje del estado y los
4 hoteles más grandes; que Armería tiene más hospedaje por habitante debido a sus playas, y que Villa de Álvarez,
aunque es muy poblado, casi no tiene hoteles.

**La privacidad.** El DENUE trae el nombre, teléfono, correo y dirección de cada negocio. En negocios chicos, como
una casa de huéspedes, ese nombre puede ser el de una persona. Por eso decidimos eliminar esos datos desde el
inicio: no los necesitábamos para el análisis y así protegemos a los dueños.

**Las reglas de las fuentes.** Todas las fuentes que consultamos cumplen con sus reglas, licencias y términos de uso.
En el caso del INEGI, sus términos permiten usar los datos siempre que se cite la fuente, se avise que los datos
fueron transformados y no se diga que el análisis es de ellos; por eso agregamos esa nota a los mapas.

## 7. Indicadores del proceso (PSP)

| Indicador | Meta | Resultado E2 |
|---|---|---|
| Q1 · Corridas de Actions en verde | ≥ 95 % | 100 % (4 de 4 corridas en verde al cierre de E2) |
| Q2 · Trazabilidad completa | 100 % | **100 %**: 7,310 / 7,310 registros de Oro con linaje verificado |
| Q3a · Defectos que llegan a `main` | ≤ 10 / KLOC | 0 conocidos; 5 registrados y corregidos antes del commit |

## 8. Siguientes pasos

1. Usar `hotel_categoria_mes.csv` para el diseño de experimentos (tipo de destino × categoría × temporada × periodo).
2. Usar `serie_colima.csv` para el pronóstico (SARIMA/SARIMAX).
3. Explorar los extractos masivos de OpenStreetMap (ODbL) para medir la renta vacacional por una vía permitida.
