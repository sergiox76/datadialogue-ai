import streamlit as st
import speech_recognition as sr
import pandas as pd
import matplotlib.pyplot as plt
from llm import pregunta_a_sql
from db import ejecutar_sql
from voice import hablar

st.set_page_config(
    page_title="QueryVoice · AI SQL Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "QueryVoice — Consulta tu base de datos con lenguaje natural y voz."}
)

# ─────────────────────────────────────────────
# 🎨 ESTILOS GLOBALES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap');

/* === ROOT VARIABLES === */
:root {
    --bg:        #0a0c10;
    --surface:   #111318;
    --border:    #1e2330;
    --accent:    #00d4aa;
    --accent2:   #7b61ff;
    --danger:    #ff4d6d;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --card:      #13161e;
    --glow:      0 0 20px rgba(0,212,170,.18);
}

/* === FONDO GLOBAL === */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'Syne', sans-serif !important; }

/* === BOTÓN COLAPSAR SIDEBAR — ocultar texto feo === */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapseButton"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    border-radius: 8px !important;
    transition: background .2s !important;
}
[data-testid="stSidebarCollapseButton"]:hover {
    background: rgba(0,212,170,.1) !important;
}
/* Ocultar el ícono SVG original de Material */
[data-testid="stSidebarCollapseButton"] svg {
    display: none !important;
}
/* Inyectar flecha ← con pseudo-elemento */
[data-testid="stSidebarCollapseButton"] button::before {
    content: '←';
    font-size: 1.25rem;
    color: var(--muted);
    line-height: 1;
    transition: color .2s, transform .2s;
    font-family: 'Syne', sans-serif;
}
[data-testid="stSidebarCollapseButton"] button:hover::before {
    color: var(--accent);
    transform: translateX(-2px);
}

/* Cuando el sidebar está colapsado, la flecha apunta → */
[data-testid="stSidebarCollapsedControl"] button::before {
    content: '→';
    font-size: 1.25rem;
    color: var(--muted);
    line-height: 1;
    transition: color .2s, transform .2s;
    font-family: 'Syne', sans-serif;
}
[data-testid="stSidebarCollapsedControl"] button:hover::before {
    color: var(--accent);
    transform: translateX(2px);
}
[data-testid="stSidebarCollapsedControl"] button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    width: 36px !important;
    height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stSidebarCollapsedControl"] svg {
    display: none !important;
}

/* === HERO HEADER === */
.hero {
    padding: 2.5rem 2rem 1.5rem;
    background: linear-gradient(135deg, #0d1117 0%, #131825 60%, #0f1620 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(0,212,170,.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(123,97,255,.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(90deg, #00d4aa, #7b61ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 .4rem;
}
.hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: .82rem;
    color: var(--muted);
    letter-spacing: .06em;
}

/* === RESPONSE CARD === */
.response-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--glow);
    animation: fadeSlide .35s ease;
}
.response-label {
    font-family: 'DM Mono', monospace;
    font-size: .72rem;
    letter-spacing: .14em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: .5rem;
}
.response-text {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
}

/* === HISTORIAL ITEMS === */
.hist-item {
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .85rem 1rem;
    margin-bottom: .7rem;
    transition: border-color .2s;
}
.hist-item:hover { border-color: var(--accent); }
.hist-q {
    font-family: 'DM Mono', monospace;
    font-size: .78rem;
    color: var(--accent);
    margin-bottom: .3rem;
}
.hist-a {
    font-size: .82rem;
    color: var(--muted);
    line-height: 1.5;
}

/* === SIDEBAR TITLE === */
.sidebar-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    letter-spacing: -.01em;
    color: var(--text);
    padding: .5rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}

/* === BOTONES === */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: .04em !important;
    border-radius: 10px !important;
    transition: all .2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,212,170,.25) !important;
}

/* === MIC BUTTON ESPECIAL === */
div[data-testid="column"]:last-child .stButton > button {
    background: linear-gradient(135deg, #00d4aa, #00b897) !important;
    color: #0a0c10 !important;
    border: none !important;
    font-size: 1.1rem !important;
    width: 100% !important;
    height: 46px !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    box-shadow: 0 0 24px rgba(0,212,170,.45) !important;
}

/* === CHAT INPUT === */
[data-testid="stChatInput"] textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: .9rem !important;
    padding: .85rem 1rem !important;
    transition: border-color .2s !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,.15) !important;
}

/* === DATAFRAME === */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* === AUDIO PLAYER === */
audio {
    border-radius: 10px !important;
    width: 100% !important;
    margin-top: .5rem !important;
    background: var(--surface) !important;
}

/* === EXPANDER === */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    background: var(--card) !important;
}

/* === ANIMACIÓN === */
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* === STATUS BADGE === */
.badge {
    display: inline-block;
    padding: .25rem .65rem;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: .7rem;
    letter-spacing: .08em;
    font-weight: 500;
}
.badge-live  { background: rgba(0,212,170,.12); color: var(--accent); border: 1px solid rgba(0,212,170,.3); }
.badge-error { background: rgba(255,77,109,.12); color: var(--danger); border: 1px solid rgba(255,77,109,.3); }

/* === DIVIDER === */
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}

/* === CLEAR BTN === */
.clear-btn .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    font-size: .8rem !important;
    width: 100% !important;
}
.clear-btn .stButton > button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🧠 CONTROL DE ESTADO
# ─────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []
if "ultima_respuesta" not in st.session_state:
    st.session_state.ultima_respuesta = None
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None
if "ultimo_df" not in st.session_state:
    st.session_state.ultimo_df = None


# ─────────────────────────────────────────────
# 🎤 VOZ A TEXTO
# ─────────────────────────────────────────────
def escuchar():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("🎤 Escuchando… habla ahora", icon="🎙️")
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language="es-ES")
        return texto
    except:
        st.toast("⚠️ No se pudo reconocer el audio", icon="⚠️")
        return None


# ─────────────────────────────────────────────
# 📊 GRÁFICA INTELIGENTE
# ─────────────────────────────────────────────
ESTILO = {
    "bg_fig":  "#13161e",
    "bg_ax":   "#0d1117",
    "accent":  "#00d4aa",
    "accent2": "#7b61ff",
    "danger":  "#ff4d6d",
    "muted":   "#6b7280",
    "border":  "#1e2330",
    "palette": ["#00d4aa","#7b61ff","#ff4d6d","#f59e0b","#38bdf8","#a3e635","#fb923c"],
}

def _base_fig(w=10, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(ESTILO["bg_fig"])
    ax.set_facecolor(ESTILO["bg_ax"])
    ax.spines[['top','right','left']].set_visible(False)
    ax.spines['bottom'].set_color(ESTILO["border"])
    ax.tick_params(colors=ESTILO["muted"], labelsize=9)
    ax.yaxis.set_tick_params(labelcolor=ESTILO["muted"])
    return fig, ax

def _detectar_tipo(df, pregunta):
    p = pregunta.lower()
    cols_num = df.select_dtypes(include=['number']).columns.tolist()
    cols_txt = df.select_dtypes(exclude=['number']).columns.tolist()
    filas = len(df)

    if filas == 1 and len(df.columns) == 1:
        return 'none'
    if any(w in p for w in ['evoluci','tendencia','tiempo','año','mes','fecha','hist']):
        return 'line'
    if any(w in p for w in ['distribuci','frecuencia','rango','histograma']):
        return 'hist'
    if any(w in p for w in ['correlaci','relaci','dispersi','scatter']):
        return 'scatter'
    if any(w in p for w in ['proporci','porcentaje','participaci','pastel','pie']):
        return 'pie'
    if filas == 1:
        return 'none'
    if filas > 30 and len(cols_num) == 1 and len(cols_txt) == 0:
        return 'hist'
    if filas <= 5 and len(cols_num) >= 1 and len(cols_txt) >= 1:
        return 'pie'
    if len(cols_num) >= 2 and len(cols_txt) == 0:
        return 'scatter'
    return 'bar'

def _grafica_barras(df, ax, col_x, col_y):
    ax.bar(df[col_x].astype(str), df[col_y],
           color=ESTILO["accent"], alpha=.85, width=.6,
           edgecolor=ESTILO["bg_fig"], linewidth=.8)
    ax.set_xlabel(col_x, color=ESTILO["muted"], fontsize=9)
    ax.set_ylabel(col_y, color=ESTILO["muted"], fontsize=9)
    plt.xticks(rotation=35, ha='right', color=ESTILO["muted"])

def _grafica_linea(df, ax, col_x, cols_y):
    for i, col in enumerate(cols_y):
        color = ESTILO["palette"][i % len(ESTILO["palette"])]
        ax.plot(df[col_x].astype(str), df[col],
                color=color, linewidth=2, marker='o',
                markersize=5, markerfacecolor=ESTILO["bg_ax"])
        ax.fill_between(range(len(df)), df[col], alpha=.08, color=color)
    ax.set_xlabel(col_x, color=ESTILO["muted"], fontsize=9)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df[col_x].astype(str), rotation=35, ha='right', color=ESTILO["muted"])
    if len(cols_y) > 1:
        ax.legend(cols_y, facecolor=ESTILO["bg_fig"], labelcolor=ESTILO["muted"], fontsize=8)

def _grafica_scatter(df, ax, col_x, col_y):
    ax.scatter(df[col_x], df[col_y],
               color=ESTILO["accent2"], alpha=.7, s=60,
               edgecolors=ESTILO["bg_fig"], linewidth=.5)
    ax.set_xlabel(col_x, color=ESTILO["muted"], fontsize=9)
    ax.set_ylabel(col_y, color=ESTILO["muted"], fontsize=9)

def _grafica_pie(df, ax, col_x, col_y):
    wedges, texts, autotexts = ax.pie(
        df[col_y], labels=df[col_x].astype(str),
        colors=ESTILO["palette"][:len(df)],
        autopct='%1.1f%%', startangle=140,
        pctdistance=.82, wedgeprops=dict(width=.6, edgecolor=ESTILO["bg_fig"])
    )
    for t in texts:     t.set_color(ESTILO["muted"]); t.set_fontsize(8)
    for t in autotexts: t.set_color('#ffffff');        t.set_fontsize(8)

def _grafica_hist(df, ax, col_y):
    ax.hist(df[col_y].dropna(), bins=20,
            color=ESTILO["accent"], alpha=.8,
            edgecolor=ESTILO["bg_fig"], linewidth=.6)
    ax.set_xlabel(col_y, color=ESTILO["muted"], fontsize=9)
    ax.set_ylabel("Frecuencia", color=ESTILO["muted"], fontsize=9)

def mostrar_grafica(df, pregunta=""):
    if df is None or df.empty:
        return
    cols_num = df.select_dtypes(include=['number']).columns.tolist()
    cols_txt = df.select_dtypes(exclude=['number']).columns.tolist()
    if not cols_num:
        return

    tipo = _detectar_tipo(df, pregunta)
    if tipo == 'none':
        return

    ICONOS  = {'bar':'📊','line':'📈','scatter':'🔵','pie':'🥧','hist':'📉'}
    NOMBRES = {'bar':'Barras','line':'Tendencia','scatter':'Dispersión','pie':'Proporción','hist':'Distribución'}
    st.markdown(f"#### {ICONOS.get(tipo,'📊')} {NOMBRES.get(tipo,'Visualización')}")

    fig, ax = _base_fig()

    if tipo == 'bar':
        col_x = cols_txt[0] if cols_txt else (df.reset_index().columns[0])
        if not cols_txt:
            df = df.reset_index()
            col_x = df.columns[0]
        _grafica_barras(df, ax, col_x, cols_num[0])

    elif tipo == 'line':
        col_x = cols_txt[0] if cols_txt else cols_num[0]
        ys = [c for c in cols_num if c != col_x] or cols_num
        _grafica_linea(df, ax, col_x, ys)

    elif tipo == 'scatter':
        cx, cy = cols_num[0], cols_num[1] if len(cols_num) > 1 else cols_num[0]
        _grafica_scatter(df, ax, cx, cy)

    elif tipo == 'pie':
        col_x = cols_txt[0] if cols_txt else cols_num[0]
        _grafica_pie(df, ax, col_x, cols_num[0])

    elif tipo == 'hist':
        _grafica_hist(df, ax, cols_num[0])

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ─────────────────────────────────────────────
# 📑 SIDEBAR — HISTORIAL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📜 Historial</div>', unsafe_allow_html=True)

    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Limpiar historial", width='stretch'):
        st.session_state.historial = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.historial:
        st.markdown(
            '<p style="font-family:\'DM Mono\',monospace;font-size:.78rem;color:#3d4555;">'
            '// Sin consultas aún</p>',
            unsafe_allow_html=True
        )
    else:
        for item in reversed(st.session_state.historial):
            st.markdown(f"""
            <div class="hist-item">
                <div class="hist-q">❯ {item['pregunta']}</div>
                <div class="hist-a">{item['respuesta']}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🖥️ ÁREA PRINCIPAL
# ─────────────────────────────────────────────

# HERO HEADER
st.markdown("""
<div class="hero">
    <div class="hero-title">QueryVoice</div>
    <div class="hero-sub">// NL → SQL · VOICE · VISUALIZATION &nbsp;|&nbsp; PostgreSQL · LLaMA3 · ElevenLabs</div>
</div>
""", unsafe_allow_html=True)

# COLUMNAS: info badges
b1, b2, b3, _ = st.columns([1, 1, 1, 4])
with b1:
    st.markdown('<span class="badge badge-live">⬤ LLM activo</span>', unsafe_allow_html=True)
with b2:
    st.markdown('<span class="badge badge-live">⬤ DB conectada</span>', unsafe_allow_html=True)
with b3:
    st.markdown('<span class="badge badge-live">⬤ Voz lista</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# RESULTADO ACTUAL
if st.session_state.ultima_respuesta:
    st.markdown(f"""
    <div class="response-card">
        <div class="response-label">🤖 Respuesta</div>
        <div class="response-text">{st.session_state.ultima_respuesta}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.ultimo_audio:
        st.audio(st.session_state.ultimo_audio, format="audio/mp3")

    if st.session_state.ultimo_df is not None and not st.session_state.ultimo_df.empty:
        with st.expander("📋 Ver tabla de datos", expanded=False):
            st.dataframe(
                st.session_state.ultimo_df,
                width='stretch',
                hide_index=True
            )
        mostrar_grafica(st.session_state.ultimo_df, st.session_state.get("ultima_pregunta", ""))

    st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🛠️ LÓGICA DE PROCESAMIENTO
# ─────────────────────────────────────────────
def procesar_peticion(texto):
    if texto:
        with st.spinner("🧠 Generando consulta SQL…"):
            sql = pregunta_a_sql(texto)
        with st.spinner("⚡ Ejecutando en la base de datos…"):
            datos = ejecutar_sql(sql)

        # datos puede ser lista de tuplas O un string (error/éxito sin filas)
        if isinstance(datos, str):
            df = pd.DataFrame()
            respuesta = datos
        elif isinstance(datos, list) and len(datos) > 0:
            try:
                df = pd.DataFrame(datos)
            except Exception:
                df = pd.DataFrame()
            try:
                valor = datos[0][0]
                respuesta = f"El resultado es {valor}"
            except Exception:
                respuesta = "Consulta ejecutada con éxito."
        else:
            df = pd.DataFrame()
            respuesta = "La consulta no devolvió resultados."

        with st.spinner("🔊 Sintetizando voz…"):
            audio = hablar(respuesta)

        st.session_state.ultima_respuesta = respuesta
        st.session_state.ultimo_audio = audio
        st.session_state.ultimo_df = df
        st.session_state.ultima_pregunta = texto

        if (len(st.session_state.historial) == 0
                or st.session_state.historial[-1]["pregunta"] != texto):
            st.session_state.historial.append({
                "pregunta": texto,
                "respuesta": respuesta
            })

        st.rerun()


# ─────────────────────────────────────────────
# 💬 INPUT: TEXTO + MICRÓFONO
# ─────────────────────────────────────────────
col_texto, col_voz = st.columns([0.87, 0.13])

with col_texto:
    pregunta_t = st.chat_input("Escribe tu pregunta en lenguaje natural…")

with col_voz:
    st.markdown('<div style="padding-top:22px"></div>', unsafe_allow_html=True)
    if st.button("🎙️", help="Hablar", width='stretch'):
        p_voz = escuchar()
        if p_voz:
            procesar_peticion(p_voz)

if pregunta_t:
    procesar_peticion(pregunta_t)