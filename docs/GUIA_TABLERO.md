# Guía del tablero · Observatorio Hotelero de Colima

**Para quién:** gerentes y dueños de hoteles, asociaciones hoteleras y la Secretaría de Turismo del Estado.
**Para qué:** saber cuándo se llenan los hoteles, qué hacer cada mes y cómo va el destino contra la competencia, con
datos oficiales que se actualizan solos cada semana.

---

## Cómo se usa (3 pasos)

1. **Elige tu destino** en el recuadro de arriba a la derecha. Por defecto aparece Manzanillo, pero funciona con
   los 64 destinos monitoreados.
2. **Recorre las pestañas de izquierda a derecha.** Van de lo general (cómo nos fue) a lo práctico (qué hago cada
   mes).
3. **Lee los recuadros de color y la ✅ Recomendación.** Ahí está la respuesta; las gráficas son la evidencia.
   Pasa el mouse sobre cualquier gráfica para ver el número exacto.

## Qué responde cada pestaña

| Pestaña | Pregunta | Qué vas a ver | Decisión que te ayuda a tomar |
|---|---|---|---|
| 📊 **Resumen** | ¿Cómo nos fue este año? | 4 indicadores (ocupación, turistas, noches por turista, % extranjeros) contra el año anterior; **lo bueno, lo preocupante y la oportunidad**; tendencia desde 2016 contra el líder | Diagnóstico rápido para una junta |
| 🗓️ **Planeador de temporadas** | ¿Qué hago cada mes? | Calendario de 12 meses en verde azulado (alta), amarillo (media) y coral (baja); cuántos cuartos quedan vacíos cada noche; acción recomendada; **botón para descargar el plan en Excel** | Cuándo subir tarifas, contratar personal eventual, hacer promociones o dar mantenimiento |
| 🌊 **Competencia** | ¿Cómo vamos contra los demás? | Ranking de ocupación con tu destino resaltado; noches por turista y % de extranjeros de cada destino | A qué mercado dirigir la promoción |
| 🗺️ **Mapa de hospedaje** | ¿Dónde está la oferta en Colima? | Los 295 lugares de hospedaje del estado (hoteles, moteles, departamentos, cabañas…) en el mapa | Ubicar a la competencia, incluida la renta vacacional |
| 🛡️ **Confiabilidad** | ¿Puedo confiar en los números? | Fuentes oficiales, registros revisados, errores apartados y rastreo de cualquier dato hasta su archivo original | Respaldar decisiones ante socios o autoridades |

## Ejemplo de uso en 1 minuto (Manzanillo)

1. **Resumen:** en 2024 se ocupó el **55 %** de los cuartos, ya más que antes de la pandemia (47 %). Lo preocupante
   es que cada turista se queda **2 noches** (antes 2.5) y sólo **4 de cada 100** son extranjeros.
2. **Planeador:** **septiembre** es el mes más flojo (43 %): cada noche quedan unos **2,500 cuartos vacíos** en el
   destino. Recomendación: promociones, convenios con empresas y escuelas, mantenimiento y vacaciones del personal.
3. **Competencia:** Manzanillo es **8.º de 14** destinos de playa del Pacífico, a **20 puntos** de Los Cabos. Los
   líderes atraen turismo extranjero y estancias más largas.

## Cómo abrirlo

Desde la carpeta del proyecto:

```bash
.venv\Scripts\python -m streamlit run dashboard/app.py
```

Se abre en el navegador en `http://localhost:8501`.

## Notas importantes

- La ocupación corresponde a **hoteles registrados ante la Secretaría de Turismo (DataTur)**; no incluye renta
  vacacional tipo Airbnb.
- El planeador usa los años **después de la pandemia (2022 en adelante)**, que reflejan mejor la demanda actual.
- La temporada es **relativa a cada destino**: "alta" son sus 4 meses más fuertes, aunque no lleguen a cierto
  porcentaje.
- Fuentes: SECTUR-DataTur (CC BY 4.0), Banco de México e INEGI. Elaboración propia; no representa una postura
  oficial de esas instituciones.
