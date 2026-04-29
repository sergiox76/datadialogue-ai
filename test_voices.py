import requests
from config import ELEVENLABS_API_KEY

url = "https://api.elevenlabs.io/v1/voices"

headers = {
    "xi-api-key": ELEVENLABS_API_KEY
}

response = requests.get(url, headers=headers)

print(response.json())