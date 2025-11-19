# app.py
import streamlit as st
import time
from datetime import datetime
import sqlite3 # <--- CORRECCIÓN CRÍTICA: Añadida la importación para el manejo de excepciones
from database import init_db, add_record
import streamlit.components.v1 as components 

# Configuración de la página
st.set_page_config(page_title="Portal de Capacitación", layout="wide")

# Inicializar la base de datos al arrancar
init_db()

# --- Definición de Videos (FR3) ---
# Estas URL deben ser enlaces de TIPO EMBED (incrustar).
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
    st.session_state.user_data = {}
    st.session_state.start_time = None

# --- VISTA 1: Formulario de Login (FR1) ---
if not st.session_state.logged_in:
    st.title("Registro de Capacitación 📝")
    st.write("Por favor, ingrese sus datos para registrar su asistencia.")
 
    with st.form("login_form"):
        # Los campos no tienen required=True en Streamlit, usamos validación manual
        nombres = st.text_input("Nombres")
        apellidos = st.text_input("Apellidos")
        cedula = st.text_input("Cédula/Documento")
        correo = st.text_input("Correo Electrónico")
        area = st.selectbox("Área", list(VIDEOS_DB.keys())) # Mejor usar las claves de VIDEOS_DB
        submitted = st.form_submit_button("Ingresar y Comenzar", type="primary")
 
        if submitted:
            # Validación manual de campos vacíos
            if not nombres or not apellidos or not cedula or not correo:
                st.error("🚨 ¡Error! Por favor, complete todos los campos obligatorios.")
            else:
                # Si todo está bien, registramos los datos y comenzamos la sesión
                st.session_state.logged_in = True
                st.session_state.user_data = {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "cedula": cedula,
                    "correo": correo,
                    "area": area
                }
                st.session_state.start_time = datetime.now()
                st.rerun()

# --- VISTA 2: Portal de Capacitación (FR2, FR3, FR4) ---
else:
    user = st.session_state.user_data
    area = user["area"]
    start_time = st.session_state.start_time

    st.title(f"Portal de Capacitación: {area} 🚀")
    st.subheader(f"Bienvenido/a, **{user['nombres']} {user['apellidos']}**")
    
    # Mostrar cronómetro (FR4)
    tiempo_transcurrido = datetime.now() - start_time
    st.info(f"⏳ Tiempo en capacitación: **{str(tiempo_transcurrido).split('.')[0]}** (Horas:Minutos:Segundos)")
    
    st.markdown("---")
    
    # Mostrar videos según el área (FR2, FR3)
    videos_del_area = VIDEOS_DB.get(area, [])
    
    if not videos_del_area:
        st.warning("⚠️ No hay videos asignados para su área en este momento.")
    else:
        for video in videos_del_area:
            st.subheader(video["titulo"])
            # Usar st.components.v1.iframe para videos de SharePoint
            # NOTA: Asegúrate de que las dimensiones sean adecuadas.
            components.iframe(video["url"], height=480, width=854, scrolling=False)
            st.markdown("---")

    # Botón para finalizar y registrar
    if st.button("He finalizado mi capacitación ✅", type="primary"):
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Preparar datos para la base de datos
        record_data = (
            user["nombres"],
            user["apellidos"],
            user["cedula"],
            user["correo"],
            user["area"],
            start_time.strftime("%Y-%m-%d %H:%M:%S"), # Formatear para mejor almacenamiento en DB
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            int(duration)
        )
        
        # Guardar en la base de datos
        try:
            add_record(record_data)
            
            # Mensaje de éxito
            st.success(f"🎉 ¡Registro completado! Tiempo total: {str(end_time - start_time).split('.')[0]}. Gracias.")
            
            # Limpiar sesión y volver al login
            st.session_state.logged_in = False
            st.session_state.user_data = {}
            st.session_state.start_time = None
            
            # Esperar 3 seg para que el usuario lea el mensaje antes de recargar
            time.sleep(3) 
            st.rerun()
            
        except sqlite3.IntegrityError:
            # Captura si la clave única (ej. cédula) ya existe
            st.warning("⚠️ Parece que ya existe un registro con esta cédula o documento. Contacte al administrador.")
        except Exception as e:
            st.error(f"❌ No se pudo guardar el registro. Error: {e}")
