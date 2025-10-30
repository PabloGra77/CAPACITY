import json, time, uuid, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

ADMIN_PIN = "goleman123"

st.set_page_config(
    page_title="GIA - Capacitaciones", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .timer-display {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        color: #667eea;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 20px;
        margin: 1rem 0;
    }
    .info-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: 1rem 0;
    }
    .video-container {
        padding: 1rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ------------------ Database Setup ------------------
DB_FILE = "gia_capacitaciones.db"

def init_database():
    """Inicializar base de datos SQLite"""
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
    """Obtener áreas desde la base de datos"""
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
    """Guardar áreas en la base de datos"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM areas")
    for nombre, videos in areas_dict.items():
        videos_json = json.dumps(videos)
        cursor.execute("INSERT INTO areas (nombre, videos) VALUES (?, ?)", (nombre, videos_json))
    conn.commit()
    conn.close()

def get_news():
    """Obtener noticias desde la base de datos"""
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
    """Guardar noticias en la base de datos"""
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
    """Agregar un registro a la base de datos"""
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
    """Obtener todos los registros como DataFrame"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM registros ORDER BY id DESC", conn)
    conn.close()
    return df

def delete_noticia(idx):
    """Eliminar una noticia por índice"""
    news = get_news()
    if 0 <= idx < len(news):
        news.pop(idx)
        save_news(news)

def seconds_to_hms(s):
    """Formatear segundos a HH:MM:SS"""
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

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("### 🎓 GIA Capacitaciones")
    
    if st.session_state.user:
        st.success(f"👤 **{st.session_state.user.get('nombres', '')}**")
        st.info(f"📍 {st.session_state.user.get('area', '')}")
        
        # Mostrar cronómetro en sidebar
        if st.session_state.timer_start:
            elapsed = int(time.time() - st.session_state.timer_start)
            st.markdown(f"### ⏱️ {seconds_to_hms(elapsed)}")
        
        st.divider()
    
    mode = st.radio(
        "📋 Navegación", 
        ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"],
        index=0
    )

# ------------------ Data ------------------
AREAS = get_areas()
NEWS = get_news()

# ------------------ Pages ------------------
def page_inicio():
    st.markdown('<h1 class="main-header">👋 Bienvenido a GIA Capacitaciones</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="info-card">
        <h3>📚 ¿Cómo funciona?</h3>
        <p><strong>Esta plataforma registra automáticamente tu tiempo de capacitación.</strong></p>
        
        <ol>
            <li><strong>Regístrate</strong> con tus datos personales</li>
            <li><strong>Selecciona tu área</strong> de capacitación</li>
            <li><strong>El cronómetro inicia automáticamente</strong> al entrar</li>
            <li><strong>Capacítate</strong> con los videos de tu área</li>
            <li><strong>Finaliza</strong> cuando termines - el tiempo se guarda automáticamente</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.button("🚀 Comenzar Capacitación", type="primary", use_container_width=True, key="start_btn")
        if st.session_state.get("start_btn"):
            st.rerun()
    
    with col2:
        st.metric("📊 Áreas Disponibles", len(AREAS))
        df = get_registros_df()
        if not df.empty:
            usuarios_unicos = df['cedula'].nunique()
            st.metric("👥 Usuarios Registrados", usuarios_unicos)
            total_finalizaciones = len(df[df['evento'] == 'finalizacion'])
            st.metric("✅ Capacitaciones Completadas", total_finalizaciones)

    if NEWS:
        st.divider()
        st.markdown("### 📢 Próximas Capacitaciones")
        for n in NEWS[:3]:
            with st.expander(f"🗓️ {n.get('titulo','Sin título')}", expanded=False):
                st.write(f"**📅 Fecha:** {n.get('fecha','')}")
                st.write(f"**💻 Plataforma:** {n.get('plataforma','')}")
                if n.get("detalle"):
                    st.write(n.get("detalle",""))

def page_registro():
    st.markdown('<h1 class="main-header">📝 Registro de Ingreso</h1>', unsafe_allow_html=True)
    
    if st.session_state.user:
        st.success("✅ Ya estás registrado en esta sesión")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre", f"{st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}")
        with col2:
            st.metric("Cédula", st.session_state.user.get('cedula'))
        with col3:
            st.metric("Área", st.session_state.user.get('area'))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 Ir a Capacitaciones", type="primary", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🔄 Nuevo Registro", use_container_width=True):
                # Guardar tiempo antes de resetear
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
    
    st.info("💡 Completa el formulario para comenzar tu capacitación")
    
    with st.form("registro_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nombres = st.text_input("👤 Nombres *", placeholder="Ej: Juan Carlos")
            cedula = st.text_input("🆔 Cédula *", placeholder="Ej: 1234567890")
            area_options = list(AREAS.keys())
            area = st.selectbox("📍 Área *", options=area_options)
        
        with col2:
            apellidos = st.text_input("👤 Apellidos *", placeholder="Ej: Pérez García")
            correo = st.text_input("📧 Correo *", placeholder="Ej: usuario@empresa.com")
        
        submitted = st.form_submit_button("🚀 Iniciar Capacitación", type="primary", use_container_width=True)
        
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
                
                # Iniciar cronómetro automáticamente
                st.session_state.timer_start = time.time()
                
                # Guardar registro de ingreso
                append_registro(
                    session_id=st.session_state.session_id,
                    **st.session_state.user,
                    evento="ingreso",
                    duracion_seg="",
                    observaciones="Registro inicial - cronómetro iniciado"
                )
                
                st.success("✅ ¡Registro exitoso! Cronómetro iniciado automáticamente")
                st.balloons()
                time.sleep(1)
                st.rerun()

def page_capacitaciones():
    st.markdown('<h1 class="main-header">🎥 Material de Capacitación</h1>', unsafe_allow_html=True)

    if not st.session_state.user:
        st.warning("⚠️ Debes registrarte primero para acceder a las capacitaciones")
        if st.button("📝 Ir a Registro", type="primary"):
            st.rerun()
        return

    area = st.session_state.user.get("area")
    
    # Calcular tiempo transcurrido
    elapsed = 0
    if st.session_state.timer_start:
        elapsed = int(time.time() - st.session_state.timer_start)
    
    # Header con info del usuario
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"### 📍 {area}")
        st.caption(f"👤 {st.session_state.user.get('nombres')} {st.session_state.user.get('apellidos')}")
    with col2:
        st.markdown(f'<div class="timer-display">{seconds_to_hms(elapsed)}</div>', unsafe_allow_html=True)
    with col3:
        if st.button("🔄", help="Actualizar tiempo"):
            st.rerun()
    
    st.divider()
    
    # Videos
    urls = AREAS.get(area, [])
    
    if not urls:
        st.warning("⚠️ No hay material de capacitación configurado para esta área")
        st.info("Contacta al administrador para agregar contenido")
    else:
        st.markdown("### 📚 Material de Capacitación")
        
        for i, u in enumerate(urls, start=1):
            with st.container():
                st.markdown(f"#### 📹 Módulo {i}")
                
                if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()):
                    st.video(u)
                elif u.lower().endswith((".mp4",".webm",".mov")):
                    st.video(u)
                else:
                    st.markdown(f"🔗 [Abrir recurso externo]({u})")
                    st.caption(f"URL: {u}")
                
                st.divider()
    
    # Botón de finalización
    st.markdown("### ✅ Finalizar Capacitación")
    st.info("⏱️ El cronómetro se detuvo automáticamente al entrar. Al finalizar, se guardará tu tiempo total de capacitación.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏁 Finalizar y Guardar Tiempo", type="primary", use_container_width=True):
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
                
                st.success(f"✅ ¡Capacitación finalizada! Tiempo total: **{seconds_to_hms(final_time)}**")
                st.balloons()
                time.sleep(2)
                
                # Resetear usuario
                st.session_state.user = {}
                st.rerun()

def page_noticias():
    st.markdown('<h1 class="main-header">📰 Noticias y Anuncios</h1>', unsafe_allow_html=True)
    
    if not NEWS:
        st.info("📭 No hay anuncios publicados en este momento")
        return
    
    for idx, n in enumerate(NEWS):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"### 🗓️ {n.get('titulo','Sin título')}")
            with col2:
                st.caption(f"#{idx+1}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 **Fecha:** {n.get('fecha','')}")
            with col2:
                st.write(f"💻 **Plataforma:** {n.get('plataforma','')}")
            
            if n.get("detalle"):
                st.markdown(n.get("detalle",""))
            
            st.divider()

def page_admin():
    st.markdown('<h1 class="main-header">🔐 Panel de Administración</h1>', unsafe_allow_html=True)
    
    pin = st.text_input("🔑 PIN de administrador", type="password", placeholder="Ingresa el PIN")
    
    if pin != ADMIN_PIN:
        st.warning("⚠️ PIN incorrecto")
        st.info("💡 PIN por defecto: **goleman123**")
        return

    st.success("✅ Acceso autorizado")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Registros", "📢 Noticias", "⚙️ Configuración"])

    with tab1:
        st.markdown("### 📊 Base de Datos de Registros")
        df = get_registros_df()
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 Total Registros", len(df))
            with col2:
                ingresos = len(df[df['evento'] == 'ingreso'])
                st.metric("🚪 Ingresos", ingresos)
            with col3:
                finalizaciones = len(df[df['evento'] == 'finalizacion'])
                st.metric("✅ Finalizaciones", finalizaciones)
            with col4:
                usuarios_unicos = df['cedula'].nunique()
                st.metric("👥 Usuarios Únicos", usuarios_unicos)
            
            st.divider()
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar Todos los Registros (CSV)", 
                csv, 
                file_name=f"registros_gia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("📭 No hay registros en la base de datos")

    with tab2:
        st.markdown("### ➕ Publicar Nueva Noticia")
        
        with st.form("news_form"):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("📌 Título *", placeholder="Ej: Capacitación en Ventas")
                fecha = st.text_input("📅 Fecha y hora *", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            with col2:
                plataforma = st.text_input("💻 Plataforma *", placeholder="Ej: Zoom, Teams, Presencial")
                detalle = st.text_area("📝 Descripción", placeholder="Detalles adicionales...")
            
            submitted = st.form_submit_button("➕ Publicar Noticia", type="primary", use_container_width=True)
            
            if submitted:
                if titulo and fecha and plataforma:
                    news = get_news()
                    news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
                    save_news(news)
                    st.success("✅ Noticia publicada exitosamente")
                    st.rerun()
                else:
                    st.error("⚠️ Completa los campos obligatorios")
        
        st.divider()
        st.markdown("### 📰 Noticias Publicadas")
        
        news_list = get_news()
        if news_list:
            for idx, n in enumerate(news_list):
                with st.expander(f"🗓️ {n.get('titulo', 'Sin título')} - {n.get('fecha', '')}"):
                    st.write(f"**Plataforma:** {n.get('plataforma', '')}")
                    st.write(f"**Detalle:** {n.get('detalle', 'N/A')}")
                    if st.button(f"🗑️ Eliminar", key=f"del_{idx}"):
                        delete_noticia(idx)
                        st.success("Noticia eliminada")
                        st.rerun()
        else:
            st.info("📭 No hay noticias publicadas")

    with tab3:
        st.markdown("### ⚙️ Configuración de Áreas y Videos")
        
        current_areas = get_areas()
        current = json.dumps(current_areas, ensure_ascii=False, indent=2)
        
        st.info("💡 Edita el JSON para agregar o modificar áreas y sus videos")
        
        edited = st.text_area(
            "JSON de configuración", 
            value=current, 
            height=400,
            help='Formato: {"Nombre del Área": ["url1", "url2", "url3"]}'
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                try:
                    new_data = json.loads(edited)
                    save_areas(new_data)
                    st.success("✅ Configuración actualizada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error en el formato JSON: {e}")
        with col2:
            if st.button("🔄 Recargar", use_container_width=True):
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
