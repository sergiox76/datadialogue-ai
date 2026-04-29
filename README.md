# QueryVoice 🎙️ · AI SQL Assistant

> Consulta tu base de datos PostgreSQL usando **lenguaje natural o voz**. El sistema traduce tu pregunta a SQL con un LLM local (LLaMA 3), ejecuta la consulta y responde en audio con voz sintética de ElevenLabs.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-LLaMA3-black?style=flat-square)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-TTS-6B21A8?style=flat-square)

---

## ✨ Características

- 💬 **Lenguaje natural → SQL** usando LLaMA 3 a través de Ollama (100% local)
- 🎤 **Entrada por voz** con reconocimiento de audio en español
- 🔊 **Respuesta en audio** sintetizada con la API de ElevenLabs
- 📊 **Visualización automática** de datos en tablas y gráficas de barras
- 📜 **Historial de consultas** persistente en la sesión
- 🌑 **UI dark premium** con diseño responsive en Streamlit

---

## 🗂️ Estructura del Proyecto

```
queryvoice/
│
├── app.py              # 🖥️  Interfaz principal (Streamlit)
├── llm.py              # 🧠  Traduce pregunta → SQL usando Ollama/LLaMA3
├── db.py               # 🗃️  Ejecuta el SQL en PostgreSQL
├── voice.py            # 🔊  Genera audio con ElevenLabs TTS
├── config.py           # ⚙️  Variables de configuración (API keys, DB)
├── main.py             # 🖥️  Versión CLI del asistente (sin Streamlit)
├── test_voices.py      # 🧪  Script para listar las voces disponibles en ElevenLabs
├── requirements.txt    # 📦  Dependencias del proyecto
└── README.md
```

---

## 🧩 Descripción de cada archivo

### `app.py` — Interfaz Web
Aplicación principal construida con **Streamlit**. Gestiona el flujo completo:
1. Recibe la pregunta (texto o voz)
2. Llama a `llm.py` para generar el SQL
3. Llama a `db.py` para ejecutarlo
4. Muestra el resultado, la tabla y la gráfica
5. Llama a `voice.py` para responder en audio
6. Mantiene el historial de consultas en `st.session_state`

### `llm.py` — Motor LLM
Envía un prompt al modelo **LLaMA 3** (corriendo localmente con Ollama) que incluye el esquema de la tabla y la pregunta del usuario. El modelo devuelve únicamente el SQL válido.

### `db.py` — Conexión a PostgreSQL
Usa **psycopg2** para conectarse a la base de datos, ejecutar el SQL generado y retornar los resultados como una lista de tuplas.

### `voice.py` — Síntesis de Voz
Llama a la API REST de **ElevenLabs** con el texto de la respuesta y guarda el audio resultante como `respuesta.mp3`. Usa el modelo `eleven_multilingual_v2` para soporte en español.

### `config.py` — Configuración
Centraliza todas las variables de entorno y configuración: credenciales de la base de datos, URL de Ollama, nombre del modelo y API key de ElevenLabs.

> ⚠️ **No subas este archivo a GitHub con credenciales reales.** Usa variables de entorno o un `.env` (ver sección de seguridad).

### `main.py` — Versión CLI
Versión de línea de comandos del asistente para pruebas sin interfaz web. Permite interactuar directamente desde la terminal.

### `test_voices.py` — Explorador de Voces
Script de utilidad para listar todas las voces disponibles en tu cuenta de ElevenLabs y obtener sus `VOICE_ID`.

---

## ⚙️ Requisitos

### Software
- Python **3.10+**
- [Ollama](https://ollama.com) instalado y corriendo con el modelo `llama3`
- PostgreSQL **13+** con tu base de datos configurada
- Cuenta en [ElevenLabs](https://elevenlabs.io) (plan gratuito funciona)

### Hardware recomendado (para LLaMA 3)
- 16 GB RAM mínimo
- GPU NVIDIA con ≥ 8 GB VRAM (opcional pero recomendado)

---

## 🚀 Instalación

### 1. Clona el repositorio
```bash
git clone https://github.com/tu-usuario/queryvoice.git
cd queryvoice
```

### 2. Crea un entorno virtual e instala dependencias
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
pip install streamlit speechrecognition pyaudio matplotlib
```

### 3. Configura Ollama con LLaMA 3
```bash
# Instalar Ollama: https://ollama.com/download
ollama pull llama3
ollama serve        # Debe quedar corriendo en http://localhost:11434
```

### 4. Configura la base de datos
```sql
-- Crea la base de datos y la tabla en PostgreSQL
CREATE DATABASE california_housing;

CREATE TABLE viviendas (
    longitude          FLOAT,
    latitude           FLOAT,
    housing_median_age FLOAT,
    total_rooms        FLOAT,
    total_bedrooms     FLOAT,
    population         FLOAT,
    households         FLOAT,
    median_income      FLOAT,
    median_house_value FLOAT
);
-- Luego importa tu CSV con COPY o pgAdmin
```

### 5. Configura tus credenciales
Edita `config.py` con tus datos reales:
```python
DB_CONFIG = {
    "host":     "localhost",
    "database": "california_housing",
    "user":     "tu_usuario",
    "password": "tu_password"
}

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "llama3"

ELEVENLABS_API_KEY = "sk_tu_api_key_aqui"
```

### 6. Ejecuta la app
```bash
streamlit run app.py
```

Abre el navegador en **http://localhost:8501**

---

## 🔒 Seguridad — Variables de Entorno (recomendado)

Para no exponer credenciales en el repositorio, usa un archivo `.env`:

```bash
pip install python-dotenv
```

Crea `.env` en la raíz:
```env
DB_HOST=localhost
DB_NAME=california_housing
DB_USER=postgres
DB_PASSWORD=tu_password
ELEVENLABS_API_KEY=sk_tu_key
```

Actualiza `config.py`:
```python
import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
```

Añade al `.gitignore`:
```
.env
config.py
respuesta.mp3
__pycache__/
venv/
```

---

## 📦 Dependencias principales

| Paquete | Uso |
|---|---|
| `streamlit` | Interfaz web interactiva |
| `psycopg2-binary` | Conexión a PostgreSQL |
| `requests` | Llamadas HTTP a Ollama y ElevenLabs |
| `pandas` | Manejo de resultados tabulares |
| `matplotlib` | Gráficas de visualización |
| `speechrecognition` | Reconocimiento de voz (Google STT) |
| `pyaudio` | Captura de audio del micrófono |

---

## 🎯 Cómo funciona (flujo completo)

```
Usuario habla o escribe
        │
        ▼
[speech_recognition]  ←── Solo si es voz
        │
        ▼
  Pregunta en texto
        │
        ▼
  [llm.py · LLaMA3]  ──► Genera SQL
        │
        ▼
  [db.py · psycopg2] ──► Ejecuta en PostgreSQL
        │
        ▼
  Resultado (datos)
        │
        ▼
  [voice.py · ElevenLabs] ──► Genera audio MP3
        │
        ▼
  [app.py · Streamlit]
    ├── Muestra respuesta en texto
    ├── Reproduce audio
    ├── Muestra tabla de datos
    ├── Genera gráfica automática
    └── Guarda en historial
```

---

## 🛠️ Ejemplo de uso

**Pregunta:**
> ¿Cuál es el valor promedio de las casas?

**SQL generado:**
```sql
SELECT AVG(median_house_value) FROM viviendas;
```

**Respuesta:**
> *"El resultado es 206855.81"*  
> 🔊 [audio reproducido automáticamente]

---

## 📝 Licencia

MIT License — libre para usar, modificar y distribuir.

---

## 🙌 Créditos

Construido con [Streamlit](https://streamlit.io) · [Ollama](https://ollama.com) · [ElevenLabs](https://elevenlabs.io) · [PostgreSQL](https://postgresql.org)
