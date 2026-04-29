import requests
from config import ELEVENLABS_API_KEY

def hablar(texto):
    VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": texto,
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        file_path = "respuesta.mp3"
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path   # 👈 CLAVE
    else:
        print("Error:", response.text)
        return None