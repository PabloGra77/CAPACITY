import json, time, uuid, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from pathlib import Path

ADMIN_PIN = "goleman123"

st.set_page_config(page_title="GIA - Capacitaciones", page_icon="🎓", layout="wide")

# ------------------ Database Setup ------------------
DB_FILE = "gia_capacitaciones.db"

def init_database():
    """Inicializar base de datos SQLite"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla de registros
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
    
    # Tabla de áreas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            videos TEXT
        )
    ''')
    
    # Tabla de noticias
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

# Inicializar DB
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
        # Inicializar con datos de ejemplo
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
    
    # Limpiar tabla
    cursor.execute("DELETE FROM areas")
    
    # Insertar áreas
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
        news.append({
            "titulo": titulo,
            "fecha": fecha,
            "plataforma": plataforma,
            "detalle": detalle
        })
    return news

def save_news(news_list):
    """Guardar noticias en la base de datos"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Limpiar tabla
    cursor.execute("DELETE FROM noticias")
    
    # Insertar noticias
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

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "accumulated_time" not in st.session_state:
    st.session_state.accumulated_time = 0

if "user" not in st.session_state:
    st.session_state.user = {}

# ------------------ Sidebar ------------------
st.sidebar.title("🎓 GIA Capacitaciones")

if st.session_state.user:
    st.sidebar.success(f"👤 {st.session_state.user.get('nombres', '')} {st.session_state.user.get('apellidos', '')}")
    st.sidebar.info(f"📍 {st.session_state.user.get('area', '')}")
    st.sidebar.divider()

mode = st.sidebar.radio("Navegación", ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"], index=0)

# ------------------ Data ------------------
AREAS = get_areas()
NEWS = get_news()

# ------------------ Pages ------------------
def page_inicio():
    st.markdown("## 👋 Bienvenido(a) a la plataforma de Capacitaciones GIA")
    st.markdown("""
Esta plataforma registra **tu ingreso** y **tiempo de capacitación**.  
Sigue estos pasos:
1. Ve a **Registro**, diligencia tus datos y elige tu **Área**.
2. Serás dirigido a **Capacitaciones** con los videos de tu área.
3. Inicia el **cronómetro** cuando comiences y finalízalo al terminar.
4. Revisa anuncios en **Noticias**.
    """)

    if NEWS:
        st.markdown("### 🗓️ Próximas noticias/eventos")
        for n in NEWS[:3]:
            with st.container():
                st.write(f"**{n.get('titulo','(sin título)')}**")
                st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
                if n.get("detalle"):
                    st.caption(n.get("detalle",""))
                st.divider()

def page_registro():
    st.markdown("## 📝 Registro de Ingreso")
    
    if st.session_state.user:
        st.info("Ya te has registrado en esta sesión.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎥 Ir a Capacitaciones", type="primary", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🔄 Nuevo registro", use_container_width=True):
                st.session_state.user = {}
                st.session_state.accumulated_time = 0
                st.session_state.timer_running = False
                st.session_state.timer_start = None
                st.rerun()
        return
    
    col1, col2 = st.columns(2)
    with col1:
        nombres = st.text_input("Nombres*", placeholder="Pablo Andrés")
        cedula = st.text_input("Cédula*", placeholder="1234567890")
        area_options = list(AREAS.keys())
        area = st.selectbox("Área*", options=area_options)
    with col2:
        apellidos = st.text_input("Apellidos*", placeholder="Granados Garay")
        correo = st.text_input("Correo*", placeholder="usuario@empresa.com")

    if st.button("🚀 Registrarme & Ir a Capacitaciones", type="primary"):
        if not (nombres and apellidos and cedula and correo and area):
            st.error("Completa todos los campos obligatorios.")
        else:
            st.session_state.user = {
                "nombres": nombres.strip(),
                "apellidos": apellidos.strip(),
                "cedula": cedula.strip(),
                "correo": correo.strip(),
                "area": area.strip()
            }
            append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="ingreso",
                duracion_seg="",
                observaciones="Registro inicial"
            )
            st.success("✅ Registro guardado!")
            time.sleep(1)
            st.rerun()

def page_capacitaciones():
    st.markdown("## 🎥 Capacitaciones por Área")

    if not st.session_state.user:
        st.info("Primero realiza el **Registro** para personalizar tus capacitaciones.")
        return

    area = st.session_state.user.get("area")
    st.info(f"📍 **Área seleccionada:** {area}")
    urls = AREAS.get(area, [])

    if not urls:
        st.warning("No hay videos configurados para esta área.")
    else:
        st.write("**Videos / Enlaces de capacitación:**")
        for i, u in enumerate(urls, start=1):
            with st.expander(f"📺 Video {i}", expanded=(i==1)):
                if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()):
                    st.video(u)
                elif u.lower().endswith((".mp4",".webm",".mov")):
                    st.video(u)
                else:
                    st.markdown(f"🔗 [{u}]({u})")

    # Cronómetro
    st.divider()
    st.markdown("### ⏱️ Cronómetro de capacitación")

    current_elapsed = st.session_state.accumulated_time
    if st.session_state.timer_running and st.session_state.timer_start is not None:
        current_elapsed += int(time.time() - st.session_state.timer_start)

    col1, col2 = st.columns([3,1])
    with col1:
        st.metric("Tiempo transcurrido", value=seconds_to_hms(current_elapsed))
    with col2:
        if st.button("🔄", help="Actualizar"):
            st.rerun()

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("▶️ Iniciar", disabled=st.session_state.timer_running, use_container_width=True):
            st.session_state.timer_running = True
            st.session_state.timer_start = time.time()
            st.toast("Cronómetro iniciado", icon="⏱️")
            st.rerun()
    with colB:
        if st.button("⏸️ Pausar", disabled=not st.session_state.timer_running, use_container_width=True):
            if st.session_state.timer_start is not None:
                st.session_state.accumulated_time += int(time.time() - st.session_state.timer_start)
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.toast("Cronómetro pausado", icon="⏸️")
            st.rerun()
    with colC:
        if st.button("🏁 Finalizar", use_container_width=True, type="primary"):
            final_time = st.session_state.accumulated_time
            if st.session_state.timer_running and st.session_state.timer_start is not None:
                final_time += int(time.time() - st.session_state.timer_start)
            
            append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="finalizacion",
                duracion_seg=final_time,
                observaciones="Capacitación finalizada"
            )
            
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.session_state.accumulated_time = 0
            
            st.success(f"✅ Capacitación finalizada. Duración: {seconds_to_hms(final_time)}")
            st.balloons()

    st.info("💡 **Tip:** Puedes pausar y reanudar el cronómetro.")

def page_noticias():
    st.markdown("## 📰 Noticias y Anuncios")
    if not NEWS:
        st.info("No hay noticias por el momento.")
        return
    for n in NEWS:
        with st.container():
            st.markdown(f"### {n.get('titulo','(sin título)')}")
            st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
            if n.get("detalle"):
                st.write(n.get("detalle",""))
            st.divider()

def page_admin():
    st.markdown("## 🔐 Admin")
    pin = st.text_input("PIN de administrador", type="password", help="PIN por defecto: goleman123")
    if pin != ADMIN_PIN:
        st.warning("Ingresa el PIN correcto para continuar.")
        st.info("💡 PIN: goleman123")
        return

    st.success("✅ Acceso concedido.")

    tab1, tab2, tab3 = st.tabs(["📥 Registros", "🗓️ Noticias", "🏷️ Áreas"])

    with tab1:
        st.subheader("Registros de Usuarios")
        df = get_registros_df()
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Registros", len(df))
            with col2:
                ingresos = len(df[df['evento'] == 'ingreso'])
                st.metric("Ingresos", ingresos)
            with col3:
                finalizaciones = len(df[df['evento'] == 'finalizacion'])
                st.metric("Finalizaciones", finalizaciones)
            with col4:
                usuarios_unicos = df['cedula'].nunique()
                st.metric("Usuarios Únicos", usuarios_unicos)
            
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar CSV completo", 
                csv, 
                file_name=f"registros_gia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("No hay registros todavía.")

    with tab2:
        st.subheader("Gestionar Noticias")
        
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título*")
            fecha = st.text_input("Fecha y hora*", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        with col2:
            plataforma = st.text_input("Plataforma*")
            detalle = st.text_area("Detalle")
        
        if st.button("➕ Agregar noticia", type="primary"):
            if titulo and fecha and plataforma:
                news = get_news()
                news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
                save_news(news)
                st.success("✅ Noticia agregada!")
                st.rerun()
            else:
                st.error("Completa los campos obligatorios.")
        
        st.divider()
        st.subheader("Noticias publicadas")
        
        news_list = get_news()
        if news_list:
            for idx, n in enumerate(news_list):
                with st.expander(f"{n.get('titulo', 'Sin título')}"):
                    st.write(f"**Fecha:** {n.get('fecha', '')}")
                    st.write(f"**Plataforma:** {n.get('plataforma', '')}")
                    st.write(f"**Detalle:** {n.get('detalle', 'N/A')}")
                    if st.button(f"🗑️ Eliminar", key=f"del_{idx}"):
                        delete_noticia(idx)
                        st.rerun()
        else:
            st.info("No hay noticias.")

    with tab3:
        st.subheader("Áreas y Videos")
        
        current_areas = get_areas()
        current = json.dumps(current_areas, ensure_ascii=False, indent=2)
        edited = st.text_area("Edita el JSON", value=current, height=300, help='Formato: {"Área": ["url1", "url2"]}')
        
        if st.button("💾 Guardar áreas", type="primary"):
            try:
                new_data = json.loads(edited)
                save_areas(new_data)
                st.success("✅ Áreas actualizadas!")
                st.rerun()
            except Exception as e:
                st.error(f"JSON inválido: {e}")

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
