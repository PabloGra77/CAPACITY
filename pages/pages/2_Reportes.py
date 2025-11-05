# pages/2_Reportes.py
import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

# --- CONFIGURACIÓN DE SEGURIDAD SIMPLE ---
# Cambia esta contraseña en tu versión final
ADMIN_PASSWORD = "admin123" 

def check_password():
    """Devuelve True si la contraseña es correcta."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Mostrar el input de contraseña
    password = st.text_input("Ingrese la contraseña de administrador:", type="password")
    
    if st.button("Acceder"):
        if password == ADMIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    
    return False

def load_data():
    """Carga todos los registros desde SQLite a un DataFrame de Pandas."""
    with sqlite3.connect('capacitacion.db') as conn:
        df = pd.read_sql_query("SELECT * FROM registros", conn)
    return df

@st.cache_data # Cachear la conversión para mejorar rendimiento
def to_excel(df):
    """Convierte un DataFrame a un archivo Excel en memoria."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Registros')
    processed_data = output.getvalue()
    return processed_data

# --- Renderizado de la Página ---
st.set_page_config(page_title="Reportes", layout="wide")
st.title("📊 Reporte de Capacitaciones")

if check_password():
    try:
        df = load_data()
        
        if df.empty:
            st.info("Aún no hay registros de capacitación.")
        else:
            st.dataframe(df)
            
            st.markdown("---")
            st.subheader("Descargar Reportes")
            
            col1, col2 = st.columns(2)
            
            # Botón de descarga CSV
            with col1:
                st.download_button(
                    label="📥 Descargar como CSV",
                    data=df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name="reporte_capacitacion.csv",
                    mime="text/csv",
                )
            
            # Botón de descarga Excel
            with col2:
                excel_data = to_excel(df)
                st.download_button(
                    label="📥 Descargar como Excel",
                    data=excel_data,
                    file_name="reporte_capacitacion.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            
            # Nota sobre PDF:
            st.warning("La exportación a PDF es más compleja y requiere librerías adicionales (como FPDF2). CSV y Excel son las opciones recomendadas y más directas.")

    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        st.info("Asegúrese de que la aplicación principal se haya ejecutado al menos una vez para crear la base de datos.")
