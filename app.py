"""
============================================================
DataDialogue AI — app.py
Aplicación Streamlit completa: texto + voz, NL→SQL, TTS
============================================================
Ejecutar: streamlit run app.py
============================================================
Tecnologías:
  • Base de datos : SQLite (por defecto) o PostgreSQL
  • LLM NL→SQL   : Ollama local / LM Studio / OpenAI
  • STT           : Whisper (local, gratis)
  • TTS           : gTTS (gratis) o ElevenLabs (premium)
============================================================
"""

import os, io, re, tempfile, time
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── Importaciones opcionales (no fallan si no están) ──────
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_OK = True
except ImportError:
    LANGCHAIN_OK = False

try:
    import whisper as openai_whisper
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False

try:
    from gtts import gTTS
    GTTS_OK = True
except ImportError:
    GTTS_OK = False

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_OK = True
except ImportError:
    ELEVENLABS_OK = False

try:
    from sqlalchemy import create_engine, text
    SQLALCHEMY_OK = True
except ImportError:
    SQLALCHEMY_OK = False

load_dotenv()

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════

# Esquema de la BD que el LLM usará para generar SQL
ESQUEMA_BD = """
Base de datos: banco

Tablas:
1. ciudad       (id_ciudad, nombre_ciudad, departamento)
2. clientes     (id_cliente, nombre, apellido, documento,
                 fecha_nacimiento, id_ciudad, telefono, correo)
3. cuentas      (id_cuenta, id_cliente, tipo_cuenta, saldo,
                 fecha_apertura, estado)
   - tipo_cuenta valores: 'Ahorros', 'Corriente'
   - estado valores: 'Activa', 'Inactiva'
4. movimientos  (id_movimiento, id_cuenta, fecha_movimiento,
                 tipo_movimiento, valor, descripcion)
   - tipo_movimiento valores: 'Consignación', 'Retiro', 'Transferencia'

Relaciones:
  clientes.id_ciudad    → ciudad.id_ciudad
  cuentas.id_cliente    → clientes.id_cliente
  movimientos.id_cuenta → cuentas.id_cuenta
"""

PROMPT_SQL = """
Eres un experto en SQL para SQLite. Convierte la pregunta del usuario en SQL válido.

NOMBRES EXACTOS DE LAS TABLAS (úsalos exactamente así, con la 's' al final):
- ciudad
- clientes
- cuentas
- movimientos

Reglas:
1. Responde SOLO con la consulta SQL, sin explicaciones ni markdown.
2. Solo consultas SELECT.
3. No uses DROP, DELETE, UPDATE, INSERT ni ALTER.
4. Usa LIMIT 100 cuando sea pertinente.
5. Usa JOINs cuando la pregunta involucre varias tablas.
6. Para filtros de texto usa LOWER() en ambos lados: LOWER(nombre_ciudad) = LOWER('bogota')
7. Si la pregunta no aplica responde: SELECT 'Pregunta fuera del alcance.' AS mensaje;

Esquema completo:
{esquema_bd}

Pregunta: {pregunta_usuario}

SQL:
"""

PROMPT_RESPUESTA = """
Eres un asistente bancario amigable y profesional.
Tu tarea es convertir un resultado tabular en una respuesta clara en español.

Reglas:
1. Responde en lenguaje natural, no en tabla.
2. Sé breve y directo.
3. No inventes datos que no estén en el resultado.
4. Si no hay resultados, dilo claramente.
5. Puedes usar listas cuando enumeres varios elementos.

Pregunta del usuario: {pregunta_usuario}
SQL ejecutado: {sql_generado}
Resultado tabular:
{resultado_tabular}

Respuesta:
"""


# ══════════════════════════════════════════════════════════
# CONEXIÓN A BASE DE DATOS
# ══════════════════════════════════════════════════════════

@st.cache_resource
def obtener_conexion():
    """Devuelve una conexión a SQLite o PostgreSQL según .env."""
    db_type = os.getenv("DB_TYPE", "sqlite").lower()

    if db_type == "postgresql":
        host     = os.getenv("PG_HOST",     "localhost")
        port     = os.getenv("PG_PORT",     "5432")
        user     = os.getenv("PG_USER",     "postgres")
        password = os.getenv("PG_PASSWORD", "")
        database = os.getenv("PG_DATABASE", "banco")
        url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(url)
        return engine.connect(), "postgresql"
    else:
        sqlite_path = os.getenv("SQLITE_PATH", "banco.db")
        if not os.path.exists(sqlite_path):
            st.error(f"❌ No se encontró '{sqlite_path}'. Ejecuta primero: python setup_db.py")
            st.stop()
        conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        return conn, "sqlite"


# ══════════════════════════════════════════════════════════
# MODELO DE LENGUAJE (LLM)
# ══════════════════════════════════════════════════════════

@st.cache_resource
def obtener_llm():
    """
    Carga el LLM según configuración:
      - Ollama:    LLM_PROVIDER=ollama,   LLM_BASE_URL=http://localhost:11434/v1
      - LM Studio: LLM_PROVIDER=lmstudio, LLM_BASE_URL=http://localhost:1234/v1
      - OpenAI:    usa OPENAI_API_KEY directamente
    """
    if not LANGCHAIN_OK:
        return None, None

    provider    = os.getenv("LLM_PROVIDER",  "openai").lower()
    model       = os.getenv("LLM_MODEL",     "gpt-4.1-mini")
    base_url    = os.getenv("LLM_BASE_URL",  None)
    api_key     = os.getenv("OPENAI_API_KEY", "")

    kwargs = {"model": model, "temperature": 0}

    if provider in ("ollama", "lmstudio"):
        # Ambos usan API compatible con OpenAI; solo cambia la base_url
        if not base_url:
            base_url = "http://localhost:11434/v1" if provider == "ollama" else "http://localhost:1234/v1"
        kwargs["base_url"] = base_url
        kwargs["api_key"]  = "ollama"  # valor dummy requerido por LangChain
    else:
        # OpenAI real
        if not api_key:
            return None, "OPENAI_API_KEY no configurada en .env"
        kwargs["api_key"] = api_key

    try:
        llm = ChatOpenAI(**kwargs)
        # Cadena NL → SQL
        cadena_sql = (
            PromptTemplate(
                input_variables=["esquema_bd", "pregunta_usuario"],
                template=PROMPT_SQL
            ) | llm | StrOutputParser()
        )
        # Cadena Resultado → Respuesta natural
        cadena_resp = (
            PromptTemplate(
                input_variables=["pregunta_usuario", "sql_generado", "resultado_tabular"],
                template=PROMPT_RESPUESTA
            ) | llm | StrOutputParser()
        )
        return (cadena_sql, cadena_resp), None
    except Exception as e:
        return None, str(e)


# ══════════════════════════════════════════════════════════
# LÓGICA PRINCIPAL
# ══════════════════════════════════════════════════════════

def limpiar_sql(texto_sql: str) -> str:
    """Elimina bloques markdown que el LLM pueda incluir."""
    sql = texto_sql.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*",    "", sql)
    sql = re.sub(r"```$",       "", sql)
    return sql.strip()


def generar_sql(cadena_sql, pregunta: str) -> str:
    sql = cadena_sql.invoke({
        "esquema_bd":       ESQUEMA_BD,
        "pregunta_usuario": pregunta
    })
    return limpiar_sql(sql)


def ejecutar_sql(conn, db_type: str, sql: str) -> pd.DataFrame:
    """Ejecuta un SELECT de forma segura y devuelve un DataFrame."""
    sql_lower = sql.strip().lower()
    if not sql_lower.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT.")
    for kw in ("drop ", "delete ", "update ", "insert ", "alter ", "truncate "):
        if kw in sql_lower:
            raise ValueError(f"Instrucción no permitida detectada: {kw.strip()}")

    if db_type == "postgresql":
        return pd.read_sql(text(sql), conn)
    else:
        return pd.read_sql_query(sql, conn)


def generar_respuesta_natural(cadena_resp, pregunta: str, sql: str, df: pd.DataFrame) -> str:
    tabla_str = df.to_string(index=False) if not df.empty else "(Sin resultados)"
    resp = cadena_resp.invoke({
        "pregunta_usuario":  pregunta,
        "sql_generado":      sql,
        "resultado_tabular": tabla_str,
    })
    return resp.strip()


# ══════════════════════════════════════════════════════════
# VOZ: TRANSCRIPCIÓN (STT) con Whisper
# ══════════════════════════════════════════════════════════

@st.cache_resource
def cargar_whisper():
    if not WHISPER_OK:
        return None
    try:
        return openai_whisper.load_model("base")  # ~140MB; usar "small" para más precisión
    except Exception:
        return None


def transcribir_audio(modelo_whisper, audio_bytes: bytes) -> str:
    """Transcribe un archivo de audio a texto usando Whisper local."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        resultado = modelo_whisper.transcribe(tmp_path, language="es")
        return resultado["text"].strip()
    finally:
        os.unlink(tmp_path)


# ══════════════════════════════════════════════════════════
# VOZ: SÍNTESIS (TTS) con gTTS o ElevenLabs
# ══════════════════════════════════════════════════════════

def texto_a_voz_gtts(texto: str) -> bytes:
    """Sintetiza texto con gTTS (gratis, no requiere API key)."""
    buf = io.BytesIO()
    tts = gTTS(text=texto, lang="es", slow=False)
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def texto_a_voz_elevenlabs(texto: str) -> bytes:
    """Sintetiza texto con ElevenLabs (alta calidad, requiere API key)."""
    api_key  = os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "XB0fDUnXU5powFXDhCwa")

    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY no configurada en .env")

    client = ElevenLabs(api_key=api_key)
    audio = client.generate(
        text=texto,
        voice=voice_id,
        model="eleven_multilingual_v2"
    )
    return b"".join(audio)


def sintetizar_voz(texto: str, motor: str) -> bytes | None:
    """Elige el motor TTS según configuración."""
    try:
        if motor == "ElevenLabs" and ELEVENLABS_OK:
            return texto_a_voz_elevenlabs(texto)
        elif motor == "gTTS" and GTTS_OK:
            return texto_a_voz_gtts(texto)
    except Exception as e:
        st.warning(f"⚠️ No se pudo generar audio: {e}")
    return None


# ══════════════════════════════════════════════════════════
# FLUJO PRINCIPAL DE CONSULTA
# ══════════════════════════════════════════════════════════

def procesar_pregunta(pregunta: str, motor_tts: str):
    """
    Ejecuta el pipeline completo:
      1. Pregunta → SQL
      2. SQL → DataFrame
      3. DataFrame → Respuesta natural
      4. Respuesta → Audio (opcional)
    """
    conn, db_type = obtener_conexion()
    cadenas, error_llm = obtener_llm()

    if error_llm or cadenas is None:
        st.error(f"❌ LLM no disponible: {error_llm or 'instala langchain-openai'}")
        return

    cadena_sql, cadena_resp = cadenas

    with st.spinner("🧠 Generando SQL..."):
        try:
            sql = generar_sql(cadena_sql, pregunta)
        except Exception as e:
            st.error(f"❌ Error generando SQL: {e}")
            return

    # Mostrar trazabilidad
    with st.expander("🔍 SQL generado", expanded=True):
        st.code(sql, language="sql")

    with st.spinner("🗄️ Consultando base de datos..."):
        try:
            df = ejecutar_sql(conn, db_type, sql)
        except Exception as e:
            st.error(f"❌ Error ejecutando SQL: {e}")
            return

    # Mostrar tabla
    st.markdown(f"**📊 Resultados** — {len(df)} registro(s) encontrado(s)")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontraron registros.")

    # Respuesta natural
    with st.spinner("💬 Generando respuesta..."):
        try:
            respuesta = generar_respuesta_natural(cadena_resp, pregunta, sql, df)
        except Exception as e:
            respuesta = f"(Error generando respuesta natural: {e})"

    st.markdown("### 🧾 Respuesta")
    st.success(respuesta)

    # Síntesis de voz
    if motor_tts != "Sin audio":
        with st.spinner(f"🔊 Sintetizando voz con {motor_tts}..."):
            audio_bytes = sintetizar_voz(respuesta, motor_tts)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")

    # Guardar en historial
    if "historial" not in st.session_state:
        st.session_state.historial = []
    st.session_state.historial.append({
        "pregunta":  pregunta,
        "sql":       sql,
        "registros": len(df),
        "respuesta": respuesta,
    })


# ══════════════════════════════════════════════════════════
# INTERFAZ STREAMLIT
# ══════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="DataDialogue AI",
        page_icon="🏦",
        layout="wide",
    )

    # ── Sidebar ───────────────────────────────────────────
    with st.sidebar:
        st.title("⚙️ Configuración")

        st.subheader("🧠 Modelo LLM")
        provider = st.selectbox(
            "Proveedor",
            ["OpenAI (nube)", "Ollama (local)", "LM Studio (local)"],
            help="Selecciona el proveedor de IA para NL→SQL"
        )
        if provider == "Ollama (local)":
            os.environ["LLM_PROVIDER"]  = "ollama"
            os.environ["LLM_BASE_URL"]  = st.text_input("URL Ollama", "http://localhost:11434/v1")
            os.environ["LLM_MODEL"]     = st.text_input("Modelo", "llama3.2")
        elif provider == "LM Studio (local)":
            os.environ["LLM_PROVIDER"]  = "lmstudio"
            os.environ["LLM_BASE_URL"]  = st.text_input("URL LM Studio", "http://localhost:1234/v1")
            os.environ["LLM_MODEL"]     = st.text_input("Modelo", "mistral-7b-instruct")
        else:
            os.environ["LLM_PROVIDER"]  = "openai"
            api_key = st.text_input("OpenAI API Key", type="password",
                                     value=os.getenv("OPENAI_API_KEY", ""))
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
            os.environ["LLM_MODEL"] = st.text_input("Modelo", "gpt-4.1-mini")

        st.divider()
        st.subheader("🎧 Síntesis de voz")
        motor_tts = st.radio(
            "Motor TTS",
            ["Sin audio", "gTTS (gratis)", "ElevenLabs (premium)"],
            help="gTTS no requiere API key. ElevenLabs requiere clave en .env"
        )
        motor_tts_clean = motor_tts.split(" ")[0]  # "gTTS" | "ElevenLabs" | "Sin"

        st.divider()
        st.subheader("ℹ️ Estado del sistema")
        st.write("LangChain:", "✅" if LANGCHAIN_OK else "❌ pip install langchain-openai")
        st.write("Whisper:",   "✅" if WHISPER_OK   else "❌ pip install openai-whisper")
        st.write("gTTS:",      "✅" if GTTS_OK       else "❌ pip install gTTS")
        st.write("ElevenLabs:","✅" if ELEVENLABS_OK else "❌ pip install elevenlabs")

    # ── Encabezado principal ──────────────────────────────
    st.title("🏦 DataDialogue AI")
    st.caption("Consulta la base de datos bancaria con lenguaje natural · texto o voz")

    # ── Tabs: Texto / Voz / Historial ────────────────────
    tab_texto, tab_voz, tab_historial = st.tabs(["💬 Texto", "🎙️ Voz", "📋 Historial"])

    # ── Tab 1: Consulta por texto ─────────────────────────
    with tab_texto:
        st.subheader("Escribe tu pregunta")
        sugerencias = [
            "¿Qué clientes viven en Bogotá?",
            "¿Cuál es el saldo total por ciudad?",
            "¿Cuántas cuentas activas hay?",
            "¿Qué movimientos tuvo Ana Gómez?",
            "¿Cuáles son las 3 cuentas con mayor saldo?",
        ]
        col1, col2 = st.columns([3, 1])
        with col1:
            pregunta_texto = st.text_input(
                "Pregunta",
                placeholder="Ej: ¿Qué clientes tienen cuenta de ahorros?",
                label_visibility="collapsed"
            )
        with col2:
            enviar = st.button("🔍 Consultar", use_container_width=True, type="primary")

        st.caption("💡 Sugerencias: " + " · ".join(f"*{s}*" for s in sugerencias[:3]))

        if enviar and pregunta_texto.strip():
            st.divider()
            procesar_pregunta(pregunta_texto.strip(), motor_tts_clean)

    # ── Tab 2: Consulta por voz ───────────────────────────
    with tab_voz:
        st.subheader("Carga un archivo de audio")

        if not WHISPER_OK:
            st.warning("⚠️ Whisper no está instalado. Ejecuta: `pip install openai-whisper`")
            st.info("También necesitas **ffmpeg**: https://ffmpeg.org/download.html")
        else:
            modelo_whisper = cargar_whisper()
            if modelo_whisper is None:
                st.error("❌ No se pudo cargar el modelo Whisper.")
            else:
                audio_file = st.file_uploader(
                    "Sube un archivo de audio (.wav, .mp3, .m4a)",
                    type=["wav", "mp3", "m4a", "ogg", "webm"],
                    help="Graba tu pregunta y súbela aquí"
                )

                if audio_file:
                    st.audio(audio_file)
                    if st.button("🎙️ Transcribir y consultar", type="primary"):
                        with st.spinner("🔊 Transcribiendo con Whisper..."):
                            try:
                                pregunta_voz = transcribir_audio(
                                    modelo_whisper,
                                    audio_file.read()
                                )
                            except Exception as e:
                                st.error(f"❌ Error en transcripción: {e}")
                                st.stop()

                        st.info(f"📝 **Texto transcrito:** {pregunta_voz}")
                        st.divider()
                        procesar_pregunta(pregunta_voz, motor_tts_clean)

    # ── Tab 3: Historial conversacional ──────────────────
    with tab_historial:
        st.subheader("📋 Historial de consultas")

        if "historial" not in st.session_state or not st.session_state.historial:
            st.info("Aún no hay consultas realizadas en esta sesión.")
        else:
            for i, item in enumerate(reversed(st.session_state.historial), 1):
                with st.expander(f"#{len(st.session_state.historial) - i + 1} — {item['pregunta'][:60]}"):
                    st.markdown(f"**Pregunta:** {item['pregunta']}")
                    st.code(item["sql"], language="sql")
                    st.markdown(f"**Registros encontrados:** {item['registros']}")
                    st.success(item["respuesta"])

            if st.button("🗑️ Limpiar historial"):
                st.session_state.historial = []
                st.rerun()


if __name__ == "__main__":
    main()
