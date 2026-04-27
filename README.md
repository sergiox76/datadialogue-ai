# 🏦 DataDialogue AI — Guía completa de configuración

> Consulta una base de datos bancaria con **lenguaje natural** (texto o voz), sin escribir SQL.

---

## 📁 Archivos del proyecto

```
datadialogue-ai/
├── requirements.txt        ← Todas las dependencias
├── .env.example            ← Plantilla de variables de entorno
├── setup_db.py             ← Crea banco.db (SQLite) con datos de ejemplo
├── postgresql_schema.sql   ← DDL completo para PostgreSQL
├── migrar_postgresql.py    ← Migra SQLite → PostgreSQL
└── app.py                  ← Aplicación Streamlit completa
```

---

## 🔁 Flujo del sistema

```
Usuario (texto o audio)
        │
        ▼
   [Whisper STT]  ◄─ solo si es voz
        │
        ▼
  Pregunta en texto
        │
        ▼
 [LLM: NL → SQL]  ◄─ Ollama / LM Studio / OpenAI
        │
        ▼
  Consulta SQL
        │
        ▼
[SQLite / PostgreSQL]
        │
        ▼
   DataFrame
        │
        ▼
[LLM: Tabla → Respuesta natural]
        │
        ▼
   Respuesta en texto
        │
        ▼
 [gTTS / ElevenLabs TTS]  ◄─ opcional
        │
        ▼
   Audio reproducible
```

---

## ⚙️ Instalación paso a paso

### 1. Pre-requisitos del sistema

| Herramienta | Para qué | Descarga |
|-------------|----------|---------|
| Python 3.10+ | Todo | https://python.org |
| ffmpeg | Whisper STT | https://ffmpeg.org/download.html |
| Ollama (opcional) | LLM local gratis | https://ollama.com |
| PostgreSQL (opcional) | BD producción | https://postgresql.org |

**Instalar ffmpeg en Windows:**
```bash
winget install ffmpeg
```
**En macOS:**
```bash
brew install ffmpeg
```
**En Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

---

### 2. Crear entorno virtual e instalar dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (macOS/Linux)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

> ⚠️ `openai-whisper` descarga ~140 MB la primera vez que lo usas.

---

### 3. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env con tu editor favorito
```

**Mínimo necesario** para empezar con SQLite + OpenAI:
```
OPENAI_API_KEY=sk-proj-tu_clave_aqui
DB_TYPE=sqlite
SQLITE_PATH=banco.db
```

---

### 4. Crear la base de datos

```bash
python setup_db.py
```
Salida esperada:
```
✅ Base de datos 'banco.db' creada y poblada correctamente.
   Tablas: ciudad (4), clientes (5), cuentas (6), movimientos (10)
```

---

### 5. Lanzar la aplicación

```bash
streamlit run app.py
```
Se abre automáticamente en: **http://localhost:8501**

---

## 🧠 Fase 4: LLM Local con Ollama

### Instalar Ollama

Descarga desde https://ollama.com e instala.

### Descargar un modelo

```bash
# Modelo liviano (~2 GB RAM) — recomendado para empezar
ollama pull llama3.2

# Modelo más preciso (~4 GB RAM)
ollama pull mistral

# Modelo más grande y capaz (~8 GB RAM)
ollama pull llama3.1:8b
```

### Verificar que Ollama corre

```bash
ollama list          # ver modelos descargados
ollama serve         # iniciar el servidor (si no corre ya)
curl http://localhost:11434/v1/models  # verificar API
```

### Configurar en .env

```
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
```

O directamente en la barra lateral de la app.

---

## 🧠 Fase 4: LLM Local con LM Studio

1. Descarga LM Studio desde https://lmstudio.ai
2. Descarga un modelo desde la pestaña "Discover" (ej. `mistral-7b-instruct`)
3. Ve a "Local Server" y haz clic en "Start Server"
4. Configura:

```
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=mistral-7b-instruct-v0.2
```

---

## 🗄️ Fase 2: Migración a PostgreSQL

### Instalar PostgreSQL

- Windows: https://www.postgresql.org/download/windows/
- macOS: `brew install postgresql`
- Ubuntu: `sudo apt install postgresql`

### Crear la base de datos

```bash
psql -U postgres
CREATE DATABASE banco;
\q
```

### Opción A: Migrar desde banco.db (si ya tienes datos)

```bash
python migrar_postgresql.py
```

### Opción B: Crear desde cero con el script SQL

```bash
psql -U postgres -d banco -f postgresql_schema.sql
```

### Configurar en .env

```
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=tu_contraseña
PG_DATABASE=banco
```

---

## 🎧 Fase 5: Síntesis de voz

### gTTS (gratis, sin API key)

Ya incluido. Solo selecciona "gTTS" en la barra lateral.

### ElevenLabs (voz de alta calidad en español)

1. Regístrate en https://elevenlabs.io (plan gratis: 10k caracteres/mes)
2. Copia tu API key
3. Configura en .env:

```
ELEVENLABS_API_KEY=tu_clave_aqui
ELEVENLABS_VOICE_ID=XB0fDUnXU5powFXDhCwa
```

**Voces en español recomendadas:**
| Nombre | ID | Acento |
|--------|-----|--------|
| Charlotte | XB0fDUnXU5powFXDhCwa | Español neutro |
| Valentino | onwK4e9ZLuTAKqWW03F9 | Español latinoamericano |

---

## ❓ Preguntas de prueba

```
¿Qué clientes viven en Bogotá?
¿Cuál es el saldo total por ciudad?
¿Cuántas cuentas activas hay?
¿Qué movimientos tuvo Ana Gómez?
¿Cuáles son las 3 cuentas con mayor saldo?
¿Cuánto dinero se consignó en abril de 2026?
¿Qué clientes tienen más de una cuenta?
Muéstrame todos los retiros mayores a 200.000
```

---

## 🐛 Solución de problemas comunes

| Error | Causa | Solución |
|-------|-------|---------|
| `banco.db not found` | No se ejecutó setup_db.py | `python setup_db.py` |
| `OPENAI_API_KEY not set` | Falta clave en .env | Agregar clave al .env |
| `Connection refused (11434)` | Ollama no corre | `ollama serve` |
| `ffmpeg not found` | ffmpeg no instalado | Instalar ffmpeg |
| `ModuleNotFoundError: whisper` | Whisper no instalado | `pip install openai-whisper` |
| SQL retorna vacío | Diferencia de mayúsculas | El modelo usa ILIKE; intenta reformular |

---

## 🏗️ Arquitectura de componentes

```
┌─────────────────────────────────────────────────┐
│                  app.py (Streamlit)              │
│                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Tab Texto│  │  Tab Voz     │  │ Historial │  │
│  └────┬─────┘  └──────┬───────┘  └───────────┘  │
│       │               │                          │
│       └───────┬────────┘                         │
│               ▼                                  │
│  ┌────────────────────────────┐                  │
│  │  procesar_pregunta()       │                  │
│  │  1. generar_sql()   → LLM  │                  │
│  │  2. ejecutar_sql()  → BD   │                  │
│  │  3. generar_respuesta()    │                  │
│  │  4. sintetizar_voz()       │                  │
│  └────────────────────────────┘                  │
└─────────────────────────────────────────────────┘
         │              │              │
    ┌────┴────┐  ┌───────┴──────┐ ┌───┴────────┐
    │ SQLite /│  │ Ollama /     │ │ gTTS /     │
    │PostgreSQL│  │ LM Studio /  │ │ ElevenLabs │
    └─────────┘  │ OpenAI       │ └────────────┘
                 └──────────────┘
```
