import json, time, uuid, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

ADMIN_PIN = "goleman123"

# Plataformas predeterminadas para todas las áreas
PLATAFORMAS_PREDETERMINADAS = [
    {
        "nombre": "360",
        "url": "https://sharepoint.com/360",
        "tipo": "predeterminado"
    },
    {
        "nombre": "Panacea",
        "url": "https://sharepoint.com/panacea",
        "tipo": "predeterminado"
    },
    {
        "nombre": "Office 365",
        "url": "https://sharepoint.com/office365",
        "tipo": "predeterminado"
    },
    {
        "nombre": "Correo Corporativo",
        "url": "https://sharepoint.com/correo",
        "tipo": "predeterminado"
    }
]

st.set_page_config(
    page_title="GIA TRAINING", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS estilo Moodle moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    .stApp {
        background: #f4f4f4;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
        color: white;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .course-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1976d2;
        transition: all 0.3s;
    }
    
    .course-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .activity-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
    }
    
    .timer-display {
        background: white;
        border: 2px solid #1976d2;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #1976d2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background: #1976d2;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: #1565c0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        border: 1px solid #ced4da;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus {
        border-color: #1976d2;
        box-shadow: 0 0 0 0.2rem rgba(25,118,210,0.25);
    }
    
    [data-testid="stSidebar"] {
        background: #2c3e50;
    }
    
    [data-testid="stSidebar"] * {
        color: white;
    }
    
    .sidebar-content {
        background: #34495e;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .breadcrumb {
        background: white;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        color: #6c757d;
    }
    
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
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
            "PPL": [],
            "Recursos Humanos": [],
            "Ventas": [],
            "Tecnología": [],
            "Finanzas": []
        }
        save_areas(default_areas)
        return default_areas
    
    areas = {}
    for nombre, videos_json in rows:
        areas[nombre] = json.loads(videos_json) if videos_json else []
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

if "page" not in st.session_state:
    st.session_state.page = "Inicio"

# ------------------ Data ------------------
AREAS = get_areas()

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("## 🎓 GIA TRAINING")
    st.markdown("---")
    
    if st.session_state.user:
        st.markdown(f"""
        <div class="sidebar-content">
            <h4>👤 Usuario</h4>
            <p><strong>{st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}</strong></p>
            <p>📍 {st.session_state.user.get('area')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            st.markdown(f"""
            <div class="sidebar-content" style="text-align: center;">
                <h4>⏱️ Tiempo</h4>
                <h2 style="color: #4caf50; margin: 0;">{seconds_to_hms(elapsed)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    st.markdown("### 📋 Navegación")
    
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.page = "Inicio"
        st.rerun()
    
    if st.button("📝 Registro", use_container_width=True):
        st.session_state.page = "Registro"
        st.rerun()
    
    if st.button("📚 Mis Capacitaciones", use_container_width=True):
        st.session_state.page = "Capacitaciones"
        st.rerun()
    
    if st.button("⚙️ Administración", use_container_width=True):
        st.session_state.page = "Admin"
        st.rerun()

# ------------------ Pages ------------------
def page_inicio():
    st.markdown('<div class="main-header">🎓 Plataforma de Capacitación GIA</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="breadcrumb">
        🏠 Inicio
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="course-card">
            <h3>👋 Bienvenido al Sistema de Capacitación</h3>
            <p>Esta plataforma te permite acceder a capacitaciones organizadas por áreas.</p>
            
            <h4>📋 Instrucciones:</h4>
            <ol>
                <li><strong>Regístrate:</strong> Ingresa tus datos personales</li>
                <li><strong>Selecciona tu área:</strong> Elige el departamento al que perteneces</li>
                <li><strong>Capacítate:</strong> Accede a los videos y recursos</li>
                <li><strong>Finaliza:</strong> Completa tu capacitación y guarda tu progreso</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Comenzar Capacitación", type="primary", use_container_width=True):
            st.session_state.page = "Registro"
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div class="course-card">
            <h3 style="text-align: center; color: #1976d2;">{len(AREAS)}</h3>
            <p style="text-align: center; margin: 0;">Áreas Disponibles</p>
        </div>
        """, unsafe_allow_html=True)
        
        df = get_registros_df()
        if not df.empty:
            usuarios = df['cedula'].nunique()
            st.markdown(f"""
            <div class="course-card">
                <h3 style="text-align: center; color: #4caf50;">{usuarios}</h3>
                <p style="text-align: center; margin: 0;">Usuarios Registrados</p>
            </div>
            """, unsafe_allow_html=True)

def page_registro():
    st.markdown('<div class="main-header">📝 Registro de Usuario</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="breadcrumb">
        🏠 Inicio / 📝 Registro
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        st.markdown(f"""
        <div class="success-box">
            <h4>✅ Registro Completado</h4>
            <p><strong>Nombre:</strong> {st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}</p>
            <p><strong>Área:</strong> {st.session_state.user.get('area')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📚 Ir a Mis Capacitaciones", type="primary", use_container_width=True):
                st.session_state.page = "Capacitaciones"
                st.rerun()
        with col2:
            if st.button("🔄 Nuevo Registro", use_container_width=True):
                if st.session_state.timer_start:
                    final_time = int(time.time() - st.session_state.timer_start)
                    append_registro(
                        session_id=st.session_state.session_id,
                        **st.session_state.user,
                        evento="cancelacion",
                        duracion_seg=final_time,
                        observaciones="Usuario canceló para nuevo registro"
                    )
                st.session_state.user = {}
                st.session_state.timer_start = None
                st.rerun()
        return
    
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Información:</strong> Completa todos los campos para acceder a las capacitaciones.
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("registro_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombres = st.text_input("Nombres *", placeholder="Juan Carlos")
            cedula = st.text_input("Cédula *", placeholder="1234567890")
            area = st.selectbox("Área *", options=list(AREAS.keys()))
        
        with col2:
            apellidos = st.text_input("Apellidos *", placeholder="Pérez García")
            correo = st.text_input("Correo Electrónico *", placeholder="usuario@empresa.com")
        
        submitted = st.form_submit_button("✅ Registrarse e Iniciar", type="primary", use_container_width=True)
        
        if submitted:
            if not (nombres and apellidos and cedula and correo and area):
                st.error("⚠️ Por favor completa todos los campos obligatorios")
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
                    observaciones="Registro inicial"
                )
                
                st.success("✅ Registro exitoso. Redirigiendo...")
                time.sleep(1)
                st.session_state.page = "Capacitaciones"
                st.rerun()

def page_capacitaciones():
    if not st.session_state.user:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ Acceso Restringido</h4>
            <p>Debes registrarte primero para acceder a las capacitaciones.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Ir a Registro", type="primary"):
            st.session_state.page = "Registro"
            st.rerun()
        return
    
    area = st.session_state.user.get("area")
    st.markdown(f'<div class="main-header">📚 Capacitaciones - {area}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="breadcrumb">
        🏠 Inicio / 📚 Mis Capacitaciones / {area}
    </div>
    """, unsafe_allow_html=True)
    
    # Cronómetro
    elapsed = 0
    if st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="course-card">
            <h4>👤 {st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}</h4>
            <p>📍 Área: {area}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="timer-display">{seconds_to_hms(elapsed)}</div>', unsafe_allow_html=True)
        if st.button("🔄"):
            st.rerun()
    
    # Plataformas predeterminadas
    st.markdown("### 📌 Plataformas Corporativas (Obligatorias)")
    
    for plat in PLATAFORMAS_PREDETERMINADAS:
        st.markdown(f"""
        <div class="activity-card">
            <h4>🎥 {plat['nombre']}</h4>
            <p>Plataforma corporativa esencial</p>
            <a href="{plat['url']}" target="_blank" style="color: #1976d2; text-decoration: none; font-weight: 500;">
                📺 Acceder a la capacitación →
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Videos específicos del área
    videos_area = AREAS.get(area, [])
    
    if videos_area:
        st.markdown(f"### 📚 Capacitaciones Específicas de {area}")
        
        for idx, video in enumerate(videos_area, 1):
            st.markdown(f"""
            <div class="activity-card">
                <h4>📹 Módulo {idx}: {video.get('nombre', 'Sin título')}</h4>
                <p>{video.get('descripcion', 'Capacitación del área')}</p>
                <a href="{video.get('url', '#')}" target="_blank" style="color: #1976d2; text-decoration: none; font-weight: 500;">
                    📺 Ver capacitación →
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    # Botón de finalización
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Importante:</strong> Asegúrate de completar todas las capacitaciones antes de finalizar.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ He Finalizado la Capacitación", type="primary", use_container_width=True):
            if st.session_state.timer_start:
                final_time = int(time.time() - st.session_state.timer_start)
                
                append_registro(
                    session_id=st.session_state.session_id,
                    **st.session_state.user,
                    evento="finalizacion",
                    duracion_seg=final_time,
                    observaciones="Capacitación completada"
                )
                
                st.session_state.timer_start = None
                st.success(f"✅ Capacitación finalizada. Tiempo total: {seconds_to_hms(final_time)}")
                st.balloons()
                time.sleep(2)
                
                st.session_state.user = {}
                st.session_state.page = "Inicio"
                st.rerun()
    
    # Auto-refresh del cronómetro
    if st.session_state.timer_start:
        time.sleep(1)
        st.rerun()

def page_admin():
    st.markdown('<div class="main-header">⚙️ Panel de Administración</div>', unsafe_allow_html=True)
    
    pin = st.text_input("🔑 PIN de Administrador", type="password")
    
    if pin != ADMIN_PIN:
        st.warning("⚠️ Ingresa el PIN correcto para continuar")
        return
    
    st.success("✅ Acceso autorizado")
    
    tab1, tab2 = st.tabs(["📊 Registros", "📹 Gestión de Áreas y Videos"])
    
    with tab1:
        st.markdown("### 📊 Registros de Capacitación")
        df = get_registros_df()
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Registros", len(df))
            with col2:
                st.metric("Ingresos", len(df[df['evento'] == 'ingreso']))
            with col3:
                st.metric("Finalizaciones", len(df[df['evento'] == 'finalizacion']))
            with col4:
                st.metric("Usuarios Únicos", df['cedula'].nunique())
            
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar Registros (CSV)",
                csv,
                file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("📭 No hay registros aún")
    
    with tab2:
        st.markdown("### 📹 Configuración de Áreas y Capacitaciones")
        
        st.markdown("""
        <div class="info-box">
            <strong>ℹ️ Información:</strong> Las plataformas corporativas (360, Panacea, Office 365, Correo) son obligatorias para todas las áreas.
            Aquí puedes agregar videos específicos adicionales para cada área.
        </div>
        """, unsafe_allow_html=True)
        
        areas_actuales = get_areas()
        area_seleccionada = st.selectbox("Seleccionar Área", list(areas_actuales.keys()))
        
        st.markdown(f"#### Videos Configurados para {area_seleccionada}")
        
        videos_actuales = areas_actuales.get(area_seleccionada, [])
        
        if videos_actuales:
            for idx, video in enumerate(videos_actuales):
                with st.expander(f"📹 {video.get('nombre', 'Video ' + str(idx+1))}"):
                    st.write(f"**URL:** {video.get('url', 'N/A')}")
                    st.write(f"**Descripción:** {video.get('descripcion', 'N/A')}")
                    if st.button(f"🗑️ Eliminar", key=f"del_video_{idx}"):
                        videos_actuales.pop(idx)
                        areas_actuales[area_seleccionada] = videos_actuales
                        save_areas(areas_actuales)
                        st.success("Video eliminado")
                        st.rerun()
        else:
            st.info("Esta área aún no tiene videos específicos configurados")
        
        st.markdown("#### ➕ Agregar Nuevo Video")
        
        with st.form("add_video_form"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre del Video *")
                nueva_url = st.text_input("URL de SharePoint *", placeholder="https://sharepoint.com/...")
            with col2:
                nueva_descripcion = st.text_area("Descripción")
            
            if st.form_submit_button("➕ Agregar Video", use_container_width=True):
                if nuevo_nombre and nueva_url:
                    nuevo_video = {
                        "nombre": nuevo_nombre,
                        "url": nueva_url,
                        "descripcion": nueva_descripcion
                    }
                    videos_actuales.append(nuevo_video)
                    areas_actuales[area_seleccionada] = videos_actuales
                    save_areas(areas_actuales)
                    st.success("✅ Video agregado exitosamente")
                    st.rerun()
                else:
                    st.error("⚠️ Completa el nombre y la URL del video")

# ------------------ Router ------------------
if st.session_state.page == "Inicio":
    page_inicio()
elif st.session_state.page == "Registro":
    page_registro()
elif st.session_state.page == "Capacitaciones":
    page_capacitaciones()
elif st.session_state.page == "Admin":
    page_admin()
