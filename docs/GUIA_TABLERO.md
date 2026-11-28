# Guía del sistema · Observatorio Hotelero de Colima

**Para quién:** gerentes y dueños de hoteles, asociaciones hoteleras y la Secretaría de Turismo del Estado.

**Qué te da:**
- **Cuánto se va a llenar** tu destino cada mes del próximo año.
- **Cuánto puede vender tu hotel** y **cuánto personal necesita**.
- **Cómo va el destino contra la competencia.**

Todo con datos oficiales que se actualizan solos cada semana.

---

## La primera pantalla (sin hacer nada)

Al abrir el sistema aparece una foto del destino con cuatro tarjetas:

| Tarjeta | Qué significa |
|---|---|
| **Ocupación del último año** | Qué parte de los cuartos se vendió, y si subió o bajó frente al año anterior |
| **Pronóstico del próximo mes** | Cuánto se espera llenar, con su rango probable |
| **Promedio pronosticado del año** | Cómo se espera que cierre el año, y cuál será el mejor mes |
| **Lugar en su grupo** | Posición del destino frente a su competencia, y quién es el líder |

Debajo aparecen **lo bueno, lo preocupante y la oportunidad**, cada una en una frase.

## Cómo se usa (3 pasos)

1. **Elige tu destino**, arriba a la izquierda. Por defecto aparece Manzanillo; funciona con los 64 destinos.
2. **Revisa el pronóstico**, en la pestaña 🔮.
3. **Planea con «Mi hotel»**: escribe tus cuartos y tu tarifa, y obtén ingresos y personal mes por mes.

## Qué hace cada pestaña

| Pestaña | Para qué sirve |
|---|---|
| 🔮 **Pronóstico** | Ocupación esperada mes a mes del próximo año, con una **banda de rango probable**. Indica qué tan preciso fue el método al pronosticar el último año real (por ejemplo, ±2.2 puntos en Manzanillo) |
| 🏨 **Mi hotel** | Eliges tu categoría (1★–5★) y escribes tus cuartos y tu tarifa. Ves:<br>• la ocupación típica de tu categoría en el destino;<br>• tu **ingreso esperado del año**, con escenario pesimista y optimista;<br>• el mes de mayor ingreso;<br>• **cuántas camaristas necesitas** cada mes. Si conoces tu ocupación real, actívala y el cálculo se ajusta a tu hotel |
| 🏨 → **Simulador** | Mueves controles y comparas contra el escenario base:<br>• "subo la tarifa 10 % en temporada alta";<br>• "bajo 15 % en temporada baja";<br>• "las promociones me dan +5 puntos de ocupación".<br>Descarga tu proyección en Excel |
| 🗓️ **Temporadas** | Calendario del año por colores (🔥 alta, ⚖️ media, 🧊 baja). Eliges un mes y ves su ocupación esperada, los cuartos vacíos por noche y **la acción recomendada** |
| 🌊 **Competencia** | Ranking del destino contra su grupo, con la recomendación basada en los líderes |
| 🗺️ **Mapa** | Los 295 lugares de hospedaje de Colima, incluida la renta vacacional, con filtro por tipo |
| 🛡️ **Confiabilidad** | Fuentes oficiales, registros revisados, errores apartados y rastreo de cualquier dato hasta su archivo original |

El botón **⬇️ Descargar plan del año**, arriba a la derecha, baja el calendario con las acciones recomendadas.

## Ejemplo de 1 minuto (Manzanillo, hotel 4★ de 60 cuartos a $1,800 la noche)

1. **Primera pantalla:** en 2024 se ocupó el **54.7 %** de los cuartos. Para 2025 se espera un promedio de
   **54.7 %**, con julio como mejor mes y septiembre como el más flojo.
2. **Pronóstico:** se espera julio en ≈ **61 %** y septiembre en ≈ **45 %**. El método se equivocó en promedio ±2.2
   puntos al pronosticar 2024.
3. **Mi hotel:** los hoteles 4★ de Manzanillo ocupan en promedio **82 %**, muy por encima de los 3★ (≈ 45 %).
   Ingreso esperado para 2025: **≈ $33.7 millones** (rango $32.0–35.5 M), con 4 camaristas por turno.
4. **Simulador:** con +10 % de tarifa en temporada alta, −15 % en baja y +5 puntos por promociones, el ingreso
   sube a **≈ $33.9 millones**.

## Cómo abrirlo

```bash
.venv\Scripts\python -m streamlit run dashboard/app.py
```

Se abre en el navegador en `http://localhost:8501`.

## Notas importantes

- La ocupación corresponde a **hoteles registrados ante la Secretaría de Turismo (DataTur)**; no incluye renta
  vacacional tipo Airbnb.
- Los datos oficiales más recientes llegan a diciembre de 2024, por eso el pronóstico cubre 2025. Cuando SECTUR
  publique datos nuevos, el sistema se actualiza solo.
- **Cómo se calcula el pronóstico:** se prueban dos métodos y se publica el que se equivocó menos al pronosticar el
  último año real:
  - SARIMAX, un modelo estadístico de series de tiempo con estacionalidad y efecto pandemia;
  - "el mismo mes del año anterior".
- **"Mi hotel" y el simulador son estimaciones para planear.** El sistema no asume cómo reaccionan los clientes a
  un cambio de precio: tú defines esos supuestos. Los datos que escribes no se guardan.
- **Fotos:** Wikimedia Commons (Ale Ramos M, CC BY-SA 4.0; Wilfredo R. Rodríguez H., CC0; Dhatier, CC BY-SA 4.0;
  Irene Soria Guzmán, CC BY 2.0).
- **Fuentes:** SECTUR-DataTur (CC BY 4.0), Banco de México e INEGI. Elaboración propia.
