import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Configuración de la página
st.set_page_config(
    page_title="Plataforma de Capacitación",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Archivos de datos
USERS_FILE = "data/usuarios_registrados.json"
ANNOUNCEMENTS_FILE = "data/anuncios.json"
SESSIONS_FILE = "data/sesiones.json"

# Crear carpeta data si no existe
os.makedirs("data", exist_ok=True)

# Áreas de capacitación con videos
TRAINING_AREAS = {
    "Recursos Humanos": [
        {"titulo": "Inducción RRHH", "url": "https://sharepoint.com/video1", "duracion": "15 min"},
        {"titulo": "Políticas de la empresa", "url": "https://sharepoint.com/video2", "duracion": "20 min"},
        {"titulo": "Beneficios y compensaciones", "url": "https://sharepoint.com/video3", "duracion": "10 min"}
    ],
    "Ventas": [
        {"titulo": "Técnicas de ventas", "url": "https://sharepoint.com/video4", "duracion": "25 min"},
        {"titulo": "CRM y gestión de clientes", "url": "https://sharepoint.com/video5", "duracion": "18 min"},
        {"titulo": "Negociación efectiva", "url": "https://sharepoint.com/video6", "duracion": "22 min"}
    ],
    "Tecnología": [
        {"titulo": "Seguridad informática", "url": "https://sharepoint.com/video7", "duracion": "30 min"},
        {"titulo": "Herramientas colaborativas", "url": "https://sharepoint.com/video8", "duracion": "15 min"},
        {"titulo": "Desarrollo ágil", "url": "https://sharepoint.com/video9", "duracion": "20 min"}
    ],
    "Finanzas": [
        {"titulo": "Gestión presupuestaria", "url": "https://sharepoint.com/video10", "duracion": "25 min"},
        {"titulo": "Análisis financiero", "url": "https://sharepoint.com/video11", "duracion": "20 min"},
        {"titulo": "Control de costos", "url": "https://sharepoint.com/video12", "duracion": "18 min"}
    ],
    "Marketing": [
        {"titulo": "Marketing digital", "url": "https://sharepoint.com/video13", "duracion": "22 min"},
        {"titulo": "Redes sociales", "url": "https://sharepoint.com/video14", "duracion": "15 min"},
        {"titulo": "Branding corporativo", "url": "https://sharepoint.com/video15", "duracion": "20 min"}
    ]
}

# Funciones de utilidad
def load_json(filepath, default=[]):
    """Cargar datos desde archivo JSON"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filepath, data):
    """Guardar datos en archivo JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_time(seconds):
    """Formatear segundos a HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_elapsed_time():
    """Calcular tiempo transcurrido"""
    if st.session_state.start_time:
        return datetime.now().timestamp() - st.session_state.start_time
    return 0

# Inicializar session_state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# CSS personalizado
st.markdown("""
    <style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📚 Capacitación")
    
    if st.button("🔐 Modo Admin" if not st.session_state.is_admin else "👤 Modo Usuario"):
        st.session_state.is_admin = not st.session_state.is_admin
        st.rerun()
    
    st.divider()
    
    if st.session_state.logged_in:
        st.success(f"👋 ¡Hola, {st.session_state.user_data['nombres']}!")
        st.info(f"📍 Área: {st.session_state.user_data['area']}")
        
        # Mostrar cronómetro (sin rerun automático)
        if st.session_state.start_time:
            elapsed = get_elapsed_time()
            st.metric("⏱️ Tiempo en plataforma", format_time(elapsed))
            
            # Botón para actualizar manualmente
            if st.button("🔄 Actualizar tiempo"):
                st.rerun()
        
        st.divider()
        if st.button("🚪 Finalizar Sesión", type="primary"):
            # Guardar tiempo de sesión
            if st.session_state.start_time:
                elapsed = get_elapsed_time()
                sessions = load_json(SESSIONS_FILE)
                sessions.append({
                    "cedula": st.session_state.user_data['cedula'],
                    "nombres": st.session_state.user_data['nombres'],
                    "apellidos": st.session_state.user_data['apellidos'],
                    "area": st.session_state.user_data['area'],
                    "tiempo_segundos": int(elapsed),
                    "fecha": datetime.now().isoformat()
                })
                save_json(SESSIONS_FILE, sessions)
                st.success(f"✅ Sesión guardada: {format_time(elapsed)}")
            
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.start_time = None
            st.rerun()

# Función para mostrar anuncios
def show_announcements():
    announcements = load_json(ANNOUNCEMENTS_FILE)
    
    if announcements:
        st.subheader("📢 Próximas Capacitaciones")
        for announcement in announcements:
            with st.container():
                st.markdown(f"### {announcement['titulo']}")
                st.write(f"📅 **Fecha:** {announcement['fecha']} a las {announcement['hora']}")
                st.write(f"💻 **Plataforma:** {announcement['plataforma']}")
                if announcement.get('descripcion'):
                    st.write(f"📝 {announcement['descripcion']}")
                st.divider()
    else:
        st.info("No hay capacitaciones programadas en este momento.")

# PANEL DE ADMINISTRACIÓN
if st.session_state.is_admin:
    st.title("🔐 Panel de Administración")
    
    tab1, tab2, tab3 = st.tabs(["📊 Registros", "📢 Anuncios", "📈 Estadísticas"])
    
    with tab1:
        st.subheader("Usuarios Registrados")
        
        users = load_json(USERS_FILE)
        sessions = load_json(SESSIONS_FILE)
        
        if users:
            df_users = pd.DataFrame(users)
            st.dataframe(df_users, use_container_width=True)
            
            # Exportar a CSV
            csv = df_users.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar registros (CSV)",
                data=csv,
                file_name=f"usuarios_capacitacion_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay usuarios registrados todavía.")
        
        st.divider()
        
        st.subheader("Sesiones de Capacitación")
        if sessions:
            df_sessions = pd.DataFrame(sessions)
            df_sessions['tiempo_formateado'] = df_sessions['tiempo_segundos'].apply(format_time)
            st.dataframe(df_sessions, use_container_width=True)
            
            csv_sessions = df_sessions.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar sesiones (CSV)",
                data=csv_sessions,
                file_name=f"sesiones_capacitacion_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay sesiones registradas todavía.")
    
    with tab2:
        st.subheader("Crear Nuevo Anuncio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            titulo = st.text_input("Título de la capacitación *")
            fecha = st.date_input("Fecha *")
            plataforma = st.text_input("Plataforma (Zoom, Teams, etc.) *")
        
        with col2:
            hora = st.time_input("Hora *")
            descripcion = st.text_area("Descripción")
        
        if st.button("Publicar Anuncio", type="primary"):
            if titulo and plataforma:
                announcements = load_json(ANNOUNCEMENTS_FILE)
                announcements.append({
                    "id": len(announcements) + 1,
                    "titulo": titulo,
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "hora": hora.strftime("%H:%M"),
                    "plataforma": plataforma,
                    "descripcion": descripcion
                })
                save_json(ANNOUNCEMENTS_FILE, announcements)
                st.success("✅ Anuncio publicado exitosamente!")
                st.rerun()
            else:
                st.error("Por favor complete los campos obligatorios.")
        
        st.divider()
        
        # Mostrar anuncios existentes
        announcements = load_json(ANNOUNCEMENTS_FILE)
        if announcements:
            st.subheader("Anuncios Publicados")
            for i, ann in enumerate(announcements):
                with st.expander(f"{ann['titulo']} - {ann['fecha']}"):
                    st.write(f"**Hora:** {ann['hora']}")
                    st.write(f"**Plataforma:** {ann['plataforma']}")
                    st.write(f"**Descripción:** {ann.get('descripcion', 'N/A')}")
                    if st.button(f"🗑️ Eliminar", key=f"del_{i}"):
                        announcements.pop(i)
                        save_json(ANNOUNCEMENTS_FILE, announcements)
                        st.rerun()
    
    with tab3:
        st.subheader("Estadísticas de Capacitación")
        
        sessions = load_json(SESSIONS_FILE)
        users = load_json(USERS_FILE)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Usuarios", len(users))
        
        with col2:
            st.metric("Total Sesiones", len(sessions))
        
        with col3:
            if sessions:
                total_time = sum(s['tiempo_segundos'] for s in sessions)
                st.metric("Tiempo Total", format_time(total_time))
        
        if sessions:
            df_sessions = pd.DataFrame(sessions)
            
            st.subheader("Tiempo por Área")
            tiempo_por_area = df_sessions.groupby('area')['tiempo_segundos'].sum().sort_values(ascending=False)
            st.bar_chart(tiempo_por_area)
            
            st.subheader("Últimas 10 Sesiones")
            st.dataframe(df_sessions.tail(10), use_container_width=True)

# VISTA PRINCIPAL (No admin)
else:
    if not st.session_state.logged_in:
        # PÁGINA DE REGISTRO
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.title("📚 Plataforma de Capacitación")
            st.subheader("Registro de Usuario")
            
            nombres = st.text_input("Nombres *")
            apellidos = st.text_input("Apellidos *")
            cedula = st.text_input("Cédula *")
            correo = st.text_input("Correo electrónico *")
            area = st.selectbox("Área *", [""] + list(TRAINING_AREAS.keys()))
            
            if st.button("🚀 Comenzar Capacitación", type="primary"):
                if all([nombres, apellidos, cedula, correo, area]):
                    # Guardar usuario
                    users = load_json(USERS_FILE)
                    user_data = {
                        "nombres": nombres,
                        "apellidos": apellidos,
                        "cedula": cedula,
                        "correo": correo,
                        "area": area,
                        "fecha_registro": datetime.now().isoformat()
                    }
                    users.append(user_data)
                    save_json(USERS_FILE, users)
                    
                    # Iniciar sesión
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_data
                    st.session_state.start_time = datetime.now().timestamp()
                    st.rerun()
                else:
                    st.error("⚠️ Por favor complete todos los campos obligatorios.")
        
        with col2:
            show_announcements()
    
    else:
        # PÁGINA DE CAPACITACIÓN
        st.title(f"🎓 Capacitación - {st.session_state.user_data['area']}")
        st.write(f"Bienvenido/a **{st.session_state.user_data['nombres']} {st.session_state.user_data['apellidos']}**")
        
        # Mostrar tiempo transcurrido actualizado
        if st.session_state.start_time:
            elapsed = get_elapsed_time()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"⏱️ Tiempo en esta sesión: **{format_time(elapsed)}**")
            with col2:
                if st.button("🔄 Actualizar"):
                    st.rerun()
        
        st.divider()
        
        videos = TRAINING_AREAS.get(st.session_state.user_data['area'], [])
        
        st.subheader("📹 Videos de Capacitación")
        
        for i, video in enumerate(videos):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {i+1}. {video['titulo']}")
                    st.write(f"⏱️ Duración: {video['duracion']}")
                with col2:
                    st.link_button("▶️ Ver Video", video['url'], use_container_width=True)
                st.divider()
        
        st.info("💡 **Nota:** El tiempo que pases en esta plataforma está siendo registrado. Asegúrate de completar todos los videos antes de finalizar la sesión.")
