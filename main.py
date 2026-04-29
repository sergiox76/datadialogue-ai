from turtle import st

from llm import pregunta_a_sql
from db import ejecutar_sql
from voice import hablar

def main():
    print("🤖 Sistema NL → SQL + Voz")
    print("Escribe 'salir' para terminar\n")

    while True:
        pregunta = input("🧠 Pregunta: ")

        if pregunta.lower() == "salir":
            break

        # 1. Generar SQL
        sql = pregunta_a_sql(pregunta)
        print("\n📜 SQL generado:\n", sql)

        # Validación básica
        if "select" not in sql.lower():
            print("⚠️ SQL inválido generado por el modelo")
            continue

        # 2. Ejecutar SQL
        resultado = ejecutar_sql(sql)
        print("\n📊 Resultado:\n", resultado)

        # Generar un texto descriptivo basado en el resultado
        texto_para_voz = f"El resultado de tu consulta es: {resultado}"

        # 3. Voz
        audio_file = hablar(texto_para_voz)

        if audio_file:
         audio_bytes = open(audio_file, "rb").read()
         st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()