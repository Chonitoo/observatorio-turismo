"""Configuración central del pipeline Bronce → Plata → Oro."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
BRONCE = DATA / "bronze"
PLATA = DATA / "silver"
ORO = DATA / "gold"
CUARENTENA = DATA / "quarantine"
REPORTES = RAIZ / "reports" / "E1"
BITACORA_BRONCE = BRONCE / "_bitacora_captura.csv"

# Periodo de análisis de la serie DataTur
PERIODO_INICIO = "2016-01"
PERIODO_FIN = "2024-12"

# --- Dominios válidos (Puerta de Calidad) -----------------------------------
TIPOS_CENTRO = ["Centros de Playa", "Ciudades"]
CATEGORIAS = ["1 estrella", "2 estrellas", "3 estrellas", "4 estrellas", "5 estrellas", "Sin categoría"]
DENSIDAD_MAX = 6.0          # turistas-noche por cuarto ocupado (más de 6 personas/cuarto es implausible)
TIPO_CAMBIO_RANGO = (5.0, 50.0)   # pesos por dólar; fuera de este rango es error de captura
INPC_RANGO = (50.0, 300.0)        # índice base 2a quincena jul-2018 = 100

# --- Imputación ------------------------------------------------------------
# Huecos internos de hasta 3 meses en una serie centro×categoría activa se imputan (MAR).
# Huecos más largos, al inicio o al final, se consideran ausencia estructural (la categoría
# no operaba o dejó de monitorearse) y NO se imputan.
HUECO_MAX_IMPUTABLE = 3

# --- Atípicos --------------------------------------------------------------
IQR_K = 1.5
Z_ROBUSTO_UMBRAL = 3.5      # Iglewicz & Hoaglin (1993)
# Choques exógenos conocidos: los atípicos en estos meses son reales y NO se corrigen.
MESES_COVID = [f"2020-{m:02d}" for m in range(3, 13)] + ["2021-01", "2021-02"]  # cierres y semáforo rojo
EVENTOS_CONOCIDOS = {  # centro → (inicio, fin, descripción)
    "Acapulco": ("2023-10", "2024-06", "Huracán Otis (categoría 5, 25-oct-2023)"),
}
VENTANA_TENDENCIA = 13      # meses de la mediana móvil centrada que estima la tendencia

# --- Jerarquías conceptuales ---------------------------------------------
# Centro turístico → entidad federativa
CENTRO_ESTADO = {
    "Acapulco": "Guerrero", "Aguascalientes": "Aguascalientes", "Bahías de Huatulco": "Oaxaca",
    "Campeche": "Campeche", "Cancún": "Quintana Roo", "Celaya": "Guanajuato",
    "Chihuahua": "Chihuahua", "Ciudad Juárez": "Chihuahua", "Ciudad de México": "Ciudad de México",
    "Coatzacoalcos": "Veracruz", "Colima": "Colima", "Comitán de Domínguez": "Chiapas",
    "Cozumel": "Quintana Roo", "Culiacán": "Sinaloa", "Durango": "Durango", "El Fuerte": "Sinaloa",
    "Guadalajara": "Jalisco", "Guanajuato": "Guanajuato", "Hermosillo": "Sonora",
    "Irapuato": "Guanajuato", "Isla Mujeres": "Quintana Roo", "Ixtapa - Zihuatanejo": "Guerrero",
    "La Paz": "Baja California Sur", "León": "Guanajuato", "Loreto": "Baja California Sur",
    "Los Cabos": "Baja California Sur", "Los Mochis": "Sinaloa", "Manzanillo": "Colima",
    "Mazatlán": "Sinaloa", "Mexicali": "Baja California", "Monterrey": "Nuevo León",
    "Morelia": "Michoacán", "Mérida": "Yucatán", "Nuevo Nayarit": "Nayarit", "Oaxaca": "Oaxaca",
    "Pachuca": "Hidalgo", "Palenque": "Chiapas", "Piedras Negras": "Coahuila",
    "Playas de Rosarito": "Baja California", "Puebla": "Puebla", "Puerto Escondido": "Oaxaca",
    "Puerto Vallarta": "Jalisco", "Querétaro": "Querétaro", "Riviera Maya": "Quintana Roo",
    "Salamanca": "Guanajuato", "San Cristóbal de las Casas": "Chiapas",
    "San Felipe": "Baja California", "San Juan de los Lagos": "Jalisco",
    "San Juan del Río": "Querétaro", "San Luis Potosí": "San Luis Potosí",
    "San Miguel de Allende": "Guanajuato", "Taxco": "Guerrero", "Tecate": "Baja California",
    "Tequisquiapan": "Querétaro", "Tijuana": "Baja California", "Tlaxcala": "Tlaxcala",
    "Toluca": "Estado de México", "Tonalá Puerto Arista": "Chiapas",
    "Tuxtla Gutiérrez": "Chiapas", "Valle de Bravo": "Estado de México",
    "Veracruz-Boca del Río": "Veracruz", "Villahermosa": "Tabasco", "Xalapa": "Veracruz",
    "Zacatecas": "Zacatecas",
}

# Entidad → región económica (regionalización del Banco de México,
# "Reporte sobre las Economías Regionales").
ESTADO_REGION = {
    **dict.fromkeys(["Baja California", "Chihuahua", "Coahuila", "Nuevo León", "Sonora",
                     "Tamaulipas"], "Norte"),
    **dict.fromkeys(["Aguascalientes", "Baja California Sur", "Colima", "Durango", "Jalisco",
                     "Michoacán", "Nayarit", "San Luis Potosí", "Sinaloa", "Zacatecas"],
                    "Centro Norte"),
    **dict.fromkeys(["Ciudad de México", "Estado de México", "Guanajuato", "Hidalgo", "Morelos",
                     "Puebla", "Querétaro", "Tlaxcala"], "Centro"),
    **dict.fromkeys(["Campeche", "Chiapas", "Guerrero", "Oaxaca", "Quintana Roo", "Tabasco",
                     "Veracruz", "Yucatán"], "Sur"),
}

# Litoral de los centros de playa (para comparar grupos en E3)
LITORAL_GOLFO_CARIBE = {"Cancún", "Cozumel", "Isla Mujeres", "Riviera Maya", "Veracruz-Boca del Río"}

# Categoría → segmento de mercado
CATEGORIA_SEGMENTO = {
    "1 estrella": "Económico", "2 estrellas": "Económico", "3 estrellas": "Medio",
    "4 estrellas": "Superior", "5 estrellas": "Superior", "Sin categoría": "Sin clasificar",
}

# Mes → temporada turística (definida en la propuesta E0 y validada en la entrevista de campo)
MES_TEMPORADA = {
    1: "Media", 2: "Media", 3: "Media", 4: "Alta", 5: "Media", 6: "Media",
    7: "Alta", 8: "Alta", 9: "Baja", 10: "Baja", 11: "Media", 12: "Alta",
}

# Discretización de la ocupación hotelera (%), umbrales de negocio
OCUPACION_CORTES = [0, 40, 60, 100.0001]
OCUPACION_ETIQUETAS = ["Baja", "Media", "Alta"]

# Grupos de comparación E3 (propuesta E0)
GRUPOS_E3 = {
    "Pacífico líder": ["Puerto Vallarta", "Nuevo Nayarit", "Los Cabos", "Mazatlán"],
    "Pacífico intermedio": ["Manzanillo", "Ixtapa - Zihuatanejo", "Bahías de Huatulco", "La Paz"],
    "Pacífico rezagado": ["Acapulco", "Puerto Escondido", "Loreto"],
}
