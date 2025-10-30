import json, time, uuid, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

ADMIN_PIN = "goleman123"

st.set_page_config(
    page_title="GIA CAPACITY", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Cyberpunk
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    * {
        font-family: 'Orbitron', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
        color: #00ffff;
    }
    
    .main-header {
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00ffff 0%, #ff00ff 50%, #00ffff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0,255,255,0.5);
        margin: 2rem 0;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 5px #00ffff); }
        to { filter: drop-shadow(0 0 20px #ff00ff); }
    }
    
    .cyber-card {
        background: rgba(26, 26, 46, 0.8);
        border: 2px solid #00ffff;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0,255,255,0.3), inset 0 0 20px rgba(0,255,255,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .cyber-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(0,255,255,0.1), transparent);
        animation: scan 3s linear infinite;
    }
    
    @keyframes scan {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    
    .timer-display {
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        color: #00ffff;
        text-shadow: 0 0 20px #00ffff, 0 0 40px #00ffff;
        padding: 2rem;
        background: rgba(0,0,0,0.5);
        border: 3px solid #00ffff;
        border-radius: 20px;
        margin: 1rem 0;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 10px #00ffff; }
        50% { box-shadow: 0 0 30px #00ffff, 0 0 50px #ff00ff; }
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #00ffff 0%, #ff00ff 100%);
        color: #0a0e27;
        border: none;
        border-radius: 10px;
        font-weight: 900;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(0,255,255,0.5);
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 30px rgba(0,255,255,0.8), 0 5px 30px rgba(255,0,255,0.5);
    }
    
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea {
        background: rgba(0,0,0,0.5);
        border: 2px solid #00ffff;
        color: #00ffff;
        border-radius: 10px;
        font-family: 'Orbitron', sans-serif;
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stTextArea>div>div>textarea:focus {
        border-color: #ff00ff;
        box-shadow: 0 0 15px rgba(255,0,255,0.5);
    }
    
    .cyber-metric {
        background: rgba(0,0,0,0.7);
        border: 2px solid #00ffff;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 0 15px rgba(0,255,255,0.3);
    }
    
    .cyber-metric h3 {
        color: #ff00ff;
        font-size: 3rem;
        margin: 0;
        text-shadow: 0 0 10px #ff00ff;
    }
    
    .cyber-metric p {
        color: #00ffff;
        font-size: 1rem;
        margin: 0;
    }
    
    .sidebar .sidebar-content {
        background: rgba(10,14,39,0.95);
        border-right: 2px solid #00ffff;
    }
    
    h1, h2, h3 {
        color: #00ffff;
        text-shadow: 0 0 10px rgba(0,255,255,0.5);
    }
    
    .stExpander {
        background: rgba(26,26,46,0.5);
        border: 1px solid #00ffff;
        border-radius: 10px;
    }
    
    .stDataFrame {
        background: rgba(0,0,0,0.5);
        border: 2px solid #00ffff;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ Database Setup ------------------
DB_FILE = "gia_capacity.db"

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

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("### ⚡ GIA CAPACITY")
    
    if st.session_state.user:
        st.success(f"👤 **{st.session_state.user.get('nombres', '')}**")
        st.info(f"📍 {st.session_state.user.get('area', '')}")
        
        if st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            st.markdown(f"### ⏱️ {seconds_to_hms(elapsed)}")
        
        st.divider()
    
    mode = st.radio(
        "📋 NAVEGACIÓN", 
        ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"],
        index=0
    )

# ------------------ Data ------------------
AREAS = get_areas()
NEWS = get_news()

# Manejar redirección
if st.session_state.redirect_to:
    mode = st.session_state.redirect_to
    st.session_state.redirect_to = None

# ------------------ Pages ------------------
def page_inicio():
    st.markdown('<h1 class="main-header">⚡ GIA CAPACITY ⚡</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="cyber-card">
    <h2 style="text-align: center; color: #ff00ff;">🚀 SISTEMA DE CAPACITACIÓN AVANZADO</h2>
    <p style="text-align: center; font-size: 1.2rem;">Plataforma de entrenamiento con registro automático de tiempo</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="cyber-card">
        <h3 style="color: #00ffff;">📋 PROTOCOLO DE CAPACITACIÓN</h3>
        <ol style="font-size: 1.1rem; line-height: 2rem;">
            <li><strong style="color: #ff00ff;">Regístrate</strong> con tus datos personales</li>
            <li><strong style="color: #ff00ff;">Selecciona tu área</strong> de capacitación</li>
            <li><strong style="color: #ff00ff;">El cronómetro inicia automáticamente</strong> al entrar</li>
            <li><strong style="color: #ff00ff;">Capacítate</strong> con los videos de tu área</li>
            <li><strong style="color: #ff00ff;">Finaliza</strong> cuando termines - el tiempo se guarda automáticamente</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 COMENZAR CAPACITACIÓN", type="primary", use_container_width=True):
            st.session_state.redirect_to = "Registro"
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div class="cyber-metric">
            <h3>{len(AREAS)}</h3>
            <p>ÁREAS ACTIVAS</p>
        </div>
        """, unsafe_allow_html=True)

    if NEWS:
        st.divider()
        st.markdown("### 📡 TRANSMISIONES RECIENTES")
        for n in NEWS[:3]:
            with st.expander(f"🗓️ {n.get('titulo','Sin título')}", expanded=False):
                st.write(f"**📅 Fecha:** {n.get('fecha','')}")
                st.write(f"**💻 Plataforma:** {n.get('plataforma','')}")
                if n.get("detalle"):
                    st.write(n.get("detalle",""))

def page_registro():
    st.markdown('<h1 class="main-header">📝 REGISTRO DE ACCESO</h1>', unsafe_allow_html=True)
    
    if st.session_state.user:
        st.success("✅ ACCESO AUTORIZADO")
        
        st.markdown("""
        <div class="cyber-card">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("USUARIO", f"{st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}")
        with col2:
            st.metric("ID", st.session_state.user.get('cedula'))
        with col3:
            st.metric("SECTOR", st.session_state.user.get('area'))
        
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
    
    st.info("💡 Ingresa tus credenciales para acceder al sistema")
    
    with st.form("registro_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nombres = st.text_input("👤 NOMBRES *", placeholder="Nombre completo")
            cedula = st.text_input("🆔 CÉDULA *", placeholder="Número de identificación")
            area_options = list(AREAS.keys())
            area = st.selectbox("📍 ÁREA *", options=area_options)
        
        with col2:
            apellidos = st.text_input("👤 APELLIDOS *", placeholder="Apellidos")
            correo = st.text_input("📧 CORREO *", placeholder="email@empresa.com")
        
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
    st.markdown('<h1 class="main-header">🎥 MÓDULOS DE ENTRENAMIENTO</h1>', unsafe_allow_html=True)

    if not st.session_state.user:
        st.warning("⚠️ ACCESO DENEGADO - REGISTRO REQUERIDO")
        if st.button("📝 IR A REGISTRO", type="primary"):
            st.session_state.redirect_to = "Registro"
            st.rerun()
        return

    area = st.session_state.user.get("area")
    
    elapsed = 0
    if st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"### 📍 SECTOR: {area}")
        st.caption(f"👤 OPERADOR: {st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}")
    with col2:
        st.markdown(f'<div class="timer-display">{seconds_to_hms(elapsed)}</div>', unsafe_allow_html=True)
    with col3:
        if st.button("🔄 SYNC", help="Actualizar cronómetro"):
            st.rerun()
    
    st.divider()
    
    urls = AREAS.get(area, [])
    
    if not urls:
        st.warning("⚠️ NO HAY CONTENIDO DISPONIBLE")
        st.info("Contacta al administrador del sistema")
    else:
        st.markdown("### 📚 CONTENIDO DE CAPACITACIÓN")
        
        for i, u in enumerate(urls, start=1):
            st.markdown(f"""
            <div class="cyber-card">
            <h3>⚡ MÓDULO {i}</h3>
            """, unsafe_allow_html=True)
            
            if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()):
                st.video(u)
            elif u.lower().endswith((".mp4",".webm",".mov")):
                st.video(u)
            else:
                st.markdown(f"🔗 [ACCEDER AL RECURSO]({u})")
                st.caption(f"URL: {u}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### ✅ FINALIZAR SESIÓN")
    st.info("⏱️ El tiempo será guardado automáticamente al finalizar")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏁 COMPLETAR CAPACITACIÓN", type="primary", use_container_width=True):
            if st.session_state.timer_start:
                final_time = int(time.time() - st.session_state.timer_start)
                
                append_registro(
                    session_id=st.session_state.session_id,
                    **st.session_state.user,
                    evento="finalizacion",
                    duracion_seg=final_time,
                    observaciones="Capacitación completada exitosamente"
                )
                
                st.session_state.timer_start = None
                
                st.success(f"✅ MISIÓN COMPLETADA - TIEMPO TOTAL: **{seconds_to_hms(final_time)}**")
                st.balloons()
                time.sleep(2)
                
                st.session_state.user = {}
                st.rerun()

def page_noticias():
    st.markdown('<h1 class="main-header">📡 TRANSMISIONES</h1>', unsafe_allow_html=True)
    
    if not NEWS:
        st.info("📭 NO HAY TRANSMISIONES ACTIVAS")
        return
    
    for idx, n in enumerate(NEWS):
        st.markdown(f"""
        <div class="cyber-card">
        <h3 style="color: #ff00ff;">🗓️ {n.get('titulo','Sin título')}</h3>
        <p><strong>📅 FECHA:</strong> {n.get('fecha','')}</p>
        <p><strong>💻 PLATAFORMA:</strong> {n.get('plataforma','')}</p>
        """, unsafe_allow_html=True)
        
        if n.get("detalle"):
            st.markdown(f"<p>{n.get('detalle','')}</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def page_admin():
    st.markdown('<h1 class="main-header">🔐 PANEL DE CONTROL</h1>', unsafe_allow_html=True)
    
    pin = st.text_input("🔑 CÓDIGO DE ACCESO", type="password", placeholder="Ingresa el PIN")
    
    if pin != ADMIN_PIN:
        st.warning("⚠️ ACCESO DENEGADO")
        return

    st.success("✅ ACCESO DE ADMINISTRADOR AUTORIZADO")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 BASE DE DATOS", "📢 TRANSMISIONES", "⚙️ CONFIGURACIÓN"])

    with tab1:
        st.markdown("### 📊 REGISTROS DEL SISTEMA")
        df = get_registros_df()
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="cyber-metric">
                    <h3>{len(df)}</h3>
                    <p>REGISTROS</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                ingresos = len(df[df['evento'] == 'ingreso'])
                st.markdown(f"""
                <div class="cyber-metric">
                    <h3>{ingresos}</h3>
                    <p>INGRESOS</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                finalizaciones = len(df[df['evento'] == 'finalizacion'])
                st.markdown(f"""
                <div class="cyber-metric">
                    <h3>{finalizaciones}</h3>
                    <p>COMPLETADOS</p>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                usuarios_unicos = df['cedula'].nunique()
                st.markdown(f"""
                <div class="cyber-metric">
                    <h3>{usuarios_unicos}</h3>
                    <p>USUARIOS</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 DESCARGAR BASE DE DATOS", 
                csv, 
                file_name=f"gia_capacity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("📭 BASE DE DATOS VACÍA")

    with tab2:
        st.markdown("### ➕ NUEVA TRANSMISIÓN")
        
        with st.form("news_form"):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("📌 TÍTULO *")
                fecha = st.text_input("📅 FECHA *", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            with col2:
                plataforma = st.text_input("💻 PLATAFORMA *")
                detalle = st.text_area("📝 DETALLES")
            
            submitted = st.form_submit_button("➕ PUBLICAR", type="primary", use_container_width=True)
            
            if submitted:
                if titulo and fecha and plataforma:
                    news = get_news()
                    news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
                    save_news(news)
                    st.success("✅ TRANSMISIÓN PUBLICADA")
                    st.rerun()
                else:
                    st.error("⚠️ CAMPOS OBLIGATORIOS INCOMPLETOS")
        
        st.divider()
        st.markdown("### 📰 TRANSMISIONES ACTIVAS")
        
        news_list = get_news()
        if news_list:
            for idx, n in enumerate(news_list):
                with st.expander(f"🗓️ {n.get('titulo', 'Sin título')}"):
                    st.write(f"**Fecha:** {n.get('fecha', '')}")
                    st.write(f"**Plataforma:** {n.get('plataforma', '')}")
                    st.write(f"**Detalle:** {n.get('detalle', 'N/A')}")
                    if st.button(f"🗑️ ELIMINAR", key=f"del_{idx}"):
                        delete_noticia(idx)
                        st.success("Transmisión eliminada")
                        st.rerun()
        else:
            st.info("📭 NO HAY TRANSMISIONES")

    with tab3:
        st.markdown("### ⚙️ CONFIGURACIÓN DE ÁREAS")
        
        current_areas = get_areas()
        current = json.dumps(current_areas, ensure_ascii=False, indent=2)
        
        st.info("💡 Formato JSON: {\"Área\": [\"url1\", \"url2\"]}")
        
        edited = st.text_area("DATOS DE CONFIGURACIÓN", value=current, height=400)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
                try:
                    new_data = json.loads(edited)
                    save_areas(new_data)
                    st.success("✅ CONFIGURACIÓN ACTUALIZADA")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ERROR EN FORMATO: {e}")
        with col2:
            if st.button("🔄 RECARGAR", use_container_width=True):
                st.rerun()

# ------------------ Router ------------------
if mode == "Inicio":
    page_inicio()
elif mode == "Registro":
    page_registro()
elif mode == "Capacitaciones":
    page_capacitaciones()
elif mode == "Noticias":
    page_noticias()
elif mode == "Admin":
    page_admin()
