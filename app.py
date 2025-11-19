# app.py
import streamlit as st
import time
from datetime import datetime
import sqlite3 
import streamlit.components.v1 as components 
# Importa las funciones de tu base de datos
from database import init_db, add_record, check_user_credentials 
# NOTA: La función check_user_credentials DEBE devolver un diccionario con 'role', 'nombres', etc.

# --- Configuración de la página ---
st.set_page_config(page_title="Portal de Capacitación", layout="wide")

# Inicializar la base de datos al arrancar
init_db()

# --- Definición de Videos (Contenido simulado) ---
VIDEOS_DB = {
    "Ventas": [
        {"titulo": "Técnicas de Cierre", "url": "https://.../embed..."},
        {"titulo": "Manejo de Objeciones", "url": "https://.../embed..."}
    ],
    "Recursos Humanos": [
        {"titulo": "Proceso de Selección", "url": "https://.../embed..."},
        {"titulo": "Evaluación de Desempeño", "url": "https://.../embed..."}
    ],
    "TI": [
        {"titulo": "Seguridad Informática", "url": "https://.../embed..."},
        {"titulo": "Introducción a Docker", "url": "https://.../embed..."}
    ]
}

# --- Lógica de Sesión ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = {} # Contendrá 'role', 'nombres', 'cedula', etc.
    st.session_state.start_time = None

# Función para cerrar sesión
def logout():
    st.session_state.logged_in = False
    st.session_state.user_data = {}
    st.session_state.start_time = None
    st.rerun()

# -------------------------------------------------------------
# --- VISTA 1: Formulario de LOGIN ---
# -------------------------------------------------------------

def show_login_page():
    st.title("Acceso al Portal de Capacitación 🔒")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")

        if submitted:
            # Llama a la función de la base de datos para verificar credenciales
            user_info = check_user_credentials(username, password)
            
            if user_info:
                st.session_state.logged_in = True
                st.session_state.user_data = user_info
                st.session_state.start_time = datetime.now()
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# -------------------------------------------------------------
# --- VISTA 2: PANEL DE ADMINISTRADOR ---
# -------------------------------------------------------------

def show_admin_panel():
    st.title("Panel de Administración ⚙️")
    st.subheader(f"Bienvenido/a, {st.session_state.user_data.get('nombres')}")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Reportes de Asistencia", "📹 Editar Videos", "👤 Gestión de Usuarios"])
    
    with tab1:
        st.header("Reportes de Asistencia")
        st.info("Aquí puedes cargar o visualizar la tabla completa de registros de capacitación.")
        # Lógica para mostrar datos de la DB

    with tab2:
        st.header("Gestión de Contenido (Videos)")
        st.info("Utiliza este formulario para añadir, editar o eliminar los enlaces de capacitación.")
        
        # Simulación de un formulario de edición
        with st.form("edit_content_form"):
            st.subheader("Modificar Videos")
            area_select = st.selectbox("Área a modificar", list(VIDEOS_DB.keys()))
            
            # Muestra los videos actuales para esa área
            st.write(f"Videos actuales para {area_select}:")
            for i, video in enumerate(VIDEOS_DB.get(area_select, [])):
                st.write(f"- {video['titulo']} ({video['url']})")
            
            st.markdown("---")
            st.text_input("Nuevo Título (si deseas añadir)")
            st.text_input("Nueva URL Embed")
            
            if st.form_submit_button("Guardar Cambios (Simulado)"):
                st.success("Cambios guardados. (Se requiere implementar lógica persistente en DB o archivo).")
        
    with tab3:
        st.header("Gestión de Usuarios y Roles")
        st.warning("Esta funcionalidad requiere acceso completo a la tabla de usuarios de la base de datos.")
        # Lógica para añadir/modificar usuarios y roles

# -------------------------------------------------------------
# --- VISTA 3: PORTAL DE CAPACITACIÓN (Usuario Normal) ---
# -------------------------------------------------------------

def show_user_portal():
    user = st.session_state.user_data
    area = user.get("area") # La función de login debe devolver 'area'
    start_time = st.session_state.start_time

    st.title(f"Portal de Capacitación: {area}")
    st.subheader(f"Bienvenido/a, **{user.get('nombres')} {user.get('apellidos')}**")
    
    # Mostrar cronómetro
    tiempo_transcurrido = datetime.now() - start_time
    st.info(f"⏳ Tiempo en capacitación: **{str(tiempo_transcurrido).split('.')[0]}** (Horas:Minutos:Segundos)")
    
    st.markdown("---")
    
    # Mostrar videos
    videos_del_area = VIDEOS_DB.get(area, [])
    
    if not videos_del_area:
        st.warning("⚠️ No hay videos asignados para su área en este momento.")
    else:
        for video in videos_del_area:
            st.subheader(video["titulo"])
            # Usar iframe para contenido incrustado
            components.iframe(video["url"], height=480, width=854, scrolling=False)
            st.markdown("---")

    # Botón para finalizar y registrar
    if st.button("He finalizado mi capacitación ✅", type="primary"):
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Preparar datos
        record_data = (
            user["nombres"], user["apellidos"], user["cedula"], 
            user["correo"], user["area"], 
            start_time.strftime("%Y-%m-%d %H:%M:%S"), 
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            int(duration)
        )
        
        # Guardar en la base de datos
        try:
            add_record(record_data)
            st.success(f"🎉 ¡Registro completado! Tiempo total: {str(end_time - start_time).split('.')[0]}. Gracias.")
            time.sleep(3) 
            logout() # Usa la función de logout para limpiar y recargar
            
        except sqlite3.IntegrityError:
            st.warning("⚠️ Ya existe un registro de capacitación para su cédula.")
        except Exception as e:
            st.error(f"❌ No se pudo guardar el registro. Error: {e}")

# -------------------------------------------------------------
# --- CONTROLADOR PRINCIPAL DE LA APP ---
# -------------------------------------------------------------

if not st.session_state.logged_in:
    show_login_page()
else:
    # Mostrar botón de cierre de sesión en la barra lateral
    st.sidebar.button("Cerrar Sesión 🚪", on_click=logout)
    
    role = st.session_state.user_data.get('role')
    
    if role == 'admin':
        show_admin_panel()
    elif role == 'user':
        show_user_portal()
    else:
        # Manejo de roles no reconocidos
        st.error("Rol de usuario no reconocido. Cerrando sesión...")
        logout()
