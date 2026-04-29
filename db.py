import psycopg2
from config import DB_CONFIG

def ejecutar_sql(sql):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(sql)

        try:
            resultados = cur.fetchall()
        except:
            resultados = "Consulta ejecutada correctamente."

        cur.close()
        conn.close()

        return resultados

    except Exception as e:
        return f"Error en la base de datos: {e}"