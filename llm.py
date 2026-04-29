import requests
from config import OLLAMA_URL, MODEL

def pregunta_a_sql(pregunta):
    prompt = f"""
    Eres un experto en SQL para PostgreSQL.

    Convierte la siguiente pregunta en una consulta SQL válida.

    Tabla: viviendas
    Columnas:
    longitude, latitude, housing_median_age,
    total_rooms, total_bedrooms, population,
    households, median_income, median_house_value

    IMPORTANTE:
    - SOLO devuelve SQL
    - No expliques nada
    - Usa nombres exactos de columnas

    Pregunta: {pregunta}
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"].strip()