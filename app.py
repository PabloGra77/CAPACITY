import json, time, uuid, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

ADMIN_PIN = "goleman123"

st.set_page_config(
    page_title="GIA TRAINING", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Cyberpunk Corporativo
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Orbitron:wght@700;900&display=swap');
    
    * {
        font-family: 'Rajdhani', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #232d3f 100%);
        color: #e0e0e0;
    }
    
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00d4ff 0%, #0066ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0,212,255,0.3);
        margin: 1.5rem 0;
        letter-spacing: 8px;
    }
    
    .cyber-card {
        background: linear-gradient(145deg, rgba(26,31,46,0.95), rgba(35,45,63,0.95));
        border-left: 4px solid #00d4ff;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(0,212,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    .cyber-card:hover {
        border-left-color: #0066ff;
        box-shadow: 0 8px 32px rgba(0,102,255,0.2), 0 0 0 1px rgba(0,212,255,0.2);
        transition: all 0.3s ease;
    }
    
    .timer-display {
        font-family: 'Orbitron', sans-serif;
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        color: #00d4ff;
        text-shadow: 0 0 20px rgba(0,212,255,0.5);
        padding: 2rem;
        background: rgba(0,0,0,0.6);
        border: 2px solid #00d4ff;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: inset 0 0 20px rgba(0,212,255,0.1);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.8rem 2rem;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 4px 15px rgba(0,102,255,0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #0066ff 0%, #0044cc 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,102,255,0.5);
    }
    
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background: rgba(15,20,25,0.8) !important;
        border: 2px solid rgba(0,212,255,0.5) !important;
        color: #ffffff !important;
        border-radius: 8px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .stTextInput>div>div>input::placeholder {
        color: rgba(255,255,255,0.4) !important;
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stTextArea>div>div>textarea:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 15px rgba(0,212,255,0.4) !important;
        background: rgba(0,0,0,0.8) !important;
        color: #00d4ff !important;
    }
    
    .stTextInput label, .stSelectbox label, .stTextArea label {
        color: #00d4ff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stSelectbox>div>div>select option {
        background: #1a1f2e !important;
        color: #ffffff !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, rgba(15,20,25,0.98), rgba(26,31,46,0.98));
        border-right: 2px solid rgba(0,212,255,0.4);
        box-shadow: 5px 0 30px rgba(0,212,255,0.2);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, rgba(15,20,25,0.98), rgba(26,31,46,0.98));
    }
    
    h1, h2, h3 {
        color: #00d4ff;
        font-weight: 700;
    }
    
    .stRadio > label {
        color: #00d4ff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
    }
    
    .stRadio > div {
        background: linear-gradient(145deg, rgba(15,20,25,0.8), rgba(26,31,46,0.6));
        border: 2px solid rgba(0,212,255,0.4);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.3), 0 0 15px rgba(0,212,255,0.1);
    }
    
    .stRadio [role="radiogroup"] label {
        color: #a0a0a0 !important;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        transition: all 0.3s ease;
        margin: 0.3rem 0;
        display: block;
        border-left: 3px solid transparent;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .stRadio [role="radiogroup"] label:hover {
        background: linear-gradient(90deg, rgba(0,212,255,0.15), transparent);
        color: #00d4ff !important;
        border-left-color: #00d4ff;
        transform: translateX(5px);
        box-shadow: 0 0 15px rgba(0,212,255,0.2);
    }
    
    .stForm {
        background: linear-gradient(145deg, rgba(26,31,46,0.95), rgba(35,45,63,0.95));
        border: 2px solid rgba(0,212,255,0.3);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    
    .stExpander {
        background: rgba(26,31,46,0.6);
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 8px;
    }
    
    .stDataFrame {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 8px;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00c864 0%, #00a854 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ Database Setup ------------------
DB_FILE = "gia_training.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            session_id TEXT,
            nombres TEXT,
            apellidos TEXT,
            cedula TEXT,
            correo TEXT,
            area TEXT,
            evento TEXT,
            duracion_seg INTEGER,
            observaciones TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            videos TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            fecha TEXT,
            plataforma TEXT,
            detalle TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# ------------------ Helpers ------------------
def get_areas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, videos FROM areas")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        default_areas = {
            "Recursos Humanos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            "Ventas": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            "Tecnología": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            "Finanzas": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            "Marketing": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
        }
        save_areas(default_areas)
        return default_areas
    
    areas = {}
    for nombre, videos_json in rows:
        areas[nombre] = json.loads(videos_json)
    return areas

def save_areas(areas_dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM areas")
    for nombre, videos in areas_dict.items():
        videos_json = json.dumps(videos)
        cursor.execute("INSERT INTO areas (nombre, videos) VALUES (?, ?)", (nombre, videos_json))
    conn.commit()
    conn.close()

def get_news():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, fecha, plataforma, detalle FROM noticias ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    news = []
    for titulo, fecha, plataforma, detalle in rows:
        news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
    return news

def save_news(news_list):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM noticias")
    for n in news_list:
        cursor.execute(
            "INSERT INTO noticias (titulo, fecha, plataforma, detalle) VALUES (?, ?, ?, ?)",
            (n.get('titulo'), n.get('fecha'), n.get('plataforma'), n.get('detalle'))
        )
    conn.commit()
    conn.close()

def append_registro(**kwargs):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registros (timestamp, session_id, nombres, apellidos, cedula, correo, area, evento, duracion_seg, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        kwargs.get("session_id", ""),
        kwargs.get("nombres", ""),
        kwargs.get("apellidos", ""),
        kwargs.get("cedula", ""),
        kwargs.get("correo", ""),
        kwargs.get("area", ""),
        kwargs.get("evento", ""),
        kwargs.get("duracion_seg", ""),
        kwargs.get("observaciones", "")
    ))
    conn.commit()
    conn.close()

def get_registros_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM registros ORDER BY id DESC", conn)
    conn.close()
    return df

def delete_noticia(idx):
    news = get_news()
    if 0 <= idx < len(news):
        news.pop(idx)
        save_news(news)

def seconds_to_hms(s):
    s = int(s)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

# ------------------ State ------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

if "user" not in st.session_state:
    st.session_state.user = {}

if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = None

# ------------------ Data ------------------
AREAS = get_areas()
NEWS = get_news()

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0; margin-bottom: 1rem;">
        <h1 style="
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            font-weight: 900;
            background: linear-gradient(90deg, #00d4ff 0%, #0066ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 3px;
            margin: 0;
        ">🎓 GIA TRAINING</h1>
        <div style="
            width: 80%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00d4ff, transparent);
            margin: 1rem auto;
            box-shadow: 0 0 10px rgba(0,212,255,0.5);
        "></div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(0,200,100,0.15), rgba(0,150,80,0.15));
            border-left: 4px solid #00c864;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        ">
            <p style="color: #00c864; font-size: 0.8rem; margin: 0; text-transform: uppercase; letter-spacing: 1px;">✓ SESIÓN ACTIVA</p>
            <h3 style="color: #ffffff; font-size: 1.1rem; margin: 0.5rem 0; font-weight: 700;">{st.session_state.user.get('nombres', '')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,102,255,0.15));
            border-left: 4px solid #00d4ff;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        ">
            <p style="color: #00d4ff; font-size: 0.8rem; margin: 0; text-transform: uppercase; letter-spacing: 1px;">ÁREA</p>
            <h3 style="color: #ffffff; font-size: 1.1rem; margin: 0.5rem 0; font-weight: 700;">{st.session_state.user.get('area', '')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            st.markdown(f"""
            <div style="
                background: rgba(0,0,0,0.6);
                border: 2px solid #00d4ff;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                text-align: center;
                box-shadow: 0 0 20px rgba(0,212,255,0.3);
            ">
                <p style="color: #a0a0a0; font-size: 0.8rem; margin: 0; text-transform: uppercase; letter-spacing: 2px;">TIEMPO</p>
                <h2 style="
                    font-family: 'Orbitron', sans-serif;
                    color: #00d4ff;
                    font-size: 2rem;
                    margin: 0.5rem 0 0 0;
                    font-weight: 900;
                    text-shadow: 0 0 15px rgba(0,212,255,0.6);
                ">{seconds_to_hms(elapsed)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(0,212,255,0.5), transparent);
            margin: 1.5rem 0;
        "></div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <p style="
        color: #00d4ff;
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
    ">📋 NAVEGACIÓN</p>
    """, unsafe_allow_html=True)
    
    mode = st.radio(
        "nav",
        ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"],
        index=0,
        label_visibility="collapsed"
    )

# Manejar redirección
if st.session_state.redirect_to:
    mode = st.session_state.redirect_to
    st.session_state.redirect_to = None

# ------------------ Pages ------------------
def page_inicio():
    st.markdown('<h1 class="main-header">GIA TRAINING</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="cyber-card">
    <h2 style="text-align: center; color: #00d4ff;">PLATAFORMA DE CAPACITACIÓN EMPRESARIAL</h2>
    <p style="text-align: center; font-size: 1.1rem; color: #a0a0a0;">Sistema inteligente de gestión y registro de capacitaciones</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="cyber-card">
        <h3 style="color: #00d4ff;">📋 PROCESO DE CAPACITACIÓN</h3>
        <ol style="font-size: 1.05rem; line-height: 1.8rem; color: #e0e0e0;">
            <li><strong style="color: #00d4ff;">Registro:</strong> Completa tus datos personales en el sistema</li>
            <li><strong style="color: #00d4ff;">Selección:</strong> Elige el área de capacitación correspondiente</li>
            <li><strong style="color: #00d4ff;">Cronómetro:</strong> El tiempo inicia automáticamente al acceder</li>
            <li><strong style="color: #00d4ff;">Capacitación:</strong> Revisa todo el material de tu área</li>
            <li><strong style="color: #00d4ff;">Finalización:</strong> Completa y guarda tu progreso automáticamente</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 COMENZAR CAPACITACIÓN", type="primary", use_container_width=True):
            st.session_state.redirect_to = "Registro"
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, rgba(0,0,0,0.6), rgba(26,31,46,0.8));
            border: 2px solid rgba(0,212,255,0.4);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
        ">
            <h3 style="
                color: #00d4ff;
                font-family: 'Orbitron', sans-serif;
                font-size: 3rem;
                margin: 0;
                font-weight: 900;
            ">{len(AREAS)}</h3>
            <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0.5rem 0 0 0; text-transform: uppercase; letter-spacing: 2px;">ÁREAS ACTIVAS</p>
        </div>
        """, unsafe_allow_html=True)

    if NEWS:
        st.divider()
        st.markdown("### 📢 ANUNCIOS Y EVENTOS")
        for n in NEWS[:3]:
            with st.expander(f"🗓️ {n.get('titulo','Sin título')}", expanded=False):
                st.write(f"**📅 Fecha:** {n.get('fecha','')}")
                st.write(f"**💻 Plataforma:** {n.get('plataforma','')}")
                if n.get("detalle"):
                    st.write(n.get("detalle",""))

def page_registro():
    st.markdown('<h1 class="main-header">REGISTRO DE ACCESO</h1>', unsafe_allow_html=True)
    
    if st.session_state.user:
        st.success("✅ ACCESO AUTORIZADO")
        
        st.markdown("""
        <div class="cyber-card">
        <h3 style="color: #00d4ff; margin-bottom: 1.5rem;">INFORMACIÓN DEL USUARIO</h3>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="text-align: center;">
                <p style="color: #a0a0a0; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem;">USUARIO</p>
                <p style="color: #00d4ff; font-size: 1.3rem; font-weight: 700;">{st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <p style="color: #a0a0a0; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem;">CÉDULA</p>
                <p style="color: #00d4ff; font-size: 1.3rem; font-weight: 700;">{st.session_state.user.get('cedula')}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="text-align: center;">
                <p style="color: #a0a0a0; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem;">ÁREA</p>
                <p style="color: #00d4ff; font-size: 1.3rem; font-weight: 700;">{st.session_state.user.get('area')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 INICIAR CAPACITACIÓN", type="primary", use_container_width=True):
                st.session_state.redirect_to = "Capacitaciones"
                st.rerun()
        with col2:
            if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
                if st.session_state.timer_start:
                    final_time = int(time.time() - st.session_state.timer_start)
                    append_registro(
                        session_id=st.session_state.session_id,
                        **st.session_state.user,
                        evento="finalizacion_auto",
                        duracion_seg=final_time,
                        observaciones="Sesión finalizada por nuevo registro"
                    )
                
                st.session_state.user = {}
                st.session_state.timer_start = None
                st.rerun()
        return
    
    st.markdown("""
    <div class="cyber-card">
    <p style="text-align: center; font-size: 1.1rem; color: #00d4ff;">💡 Ingresa tus credenciales para acceder al sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("registro_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nombres = st.text_input("👤 NOMBRES *", placeholder="Ej: Juan Carlos")
            cedula = st.text_input("🆔 CÉDULA *", placeholder="Ej: 1234567890")
            area_options = list(AREAS.keys())
            area = st.selectbox("📍 ÁREA *", options=area_options)
        
        with col2:
            apellidos = st.text_input("👤 APELLIDOS *", placeholder="Ej: Pérez García")
            correo = st.text_input("📧 CORREO *", placeholder="Ej: usuario@empresa.com")
        
        submitted = st.form_submit_button("⚡ INICIAR SESIÓN", type="primary", use_container_width=True)
        
        if submitted:
            if not (nombres and apellidos and cedula and correo and area):
                st.error("⚠️ TODOS LOS CAMPOS SON OBLIGATORIOS")
            else:
                st.session_state.user = {
                    "nombres": nombres.strip(),
                    "apellidos": apellidos.strip(),
                    "cedula": cedula.strip(),
                    "correo": correo.strip(),
                    "area": area.strip()
                }
                
                st.session_state.timer_start = time.time()
                
                append_registro(
                    session_id=st.session_state.session_id,
                    **st.session_state.user,
                    evento="ingreso",
                    duracion_seg="",
                    observaciones="Registro inicial - cronómetro iniciado"
                )
                
                st.success("✅ ACCESO CONCEDIDO")
                st.balloons()
                time.sleep(1)
                st.session_state.redirect_to = "Capacitaciones"
                st.rerun()

def page_capacitaciones():
    st.markdown('<h1 class="main-header">MÓDULOS DE CAPACITACIÓN</h1>', unsafe_allow_html=True)

    if not st.session_state.user:
        st.markdown("""
        <div class="cyber-card">
        <h3 style="color: #ffc107; text-align: center;">⚠️ ACCESO DENEGADO</h3>
        <p style="text-align: center; color: #e0e0e0;">Debes registrarte para acceder al contenido de capacitación</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 IR A REGISTRO", type="primary"):
            st.session_state.redirect_to = "Registro"
            st.rerun()
        return

    area = st.session_state.user.get("area")
    
    elapsed = 0
    if st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
    
    st.markdown("""
    <div class="cyber-card">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"""
        <div>
