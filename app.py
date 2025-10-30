import os, json, time, uuid
from datetime import datetime
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
AREAS_FILE = os.path.join(DATA_DIR, "areas.json")
NEWS_FILE = os.path.join(DATA_DIR, "news.json")
REG_FILE = os.path.join(DATA_DIR, "registros.csv")

ADMIN_PIN = os.getenv("GIA_ADMIN_PIN", "goleman123")

st.set_page_config(page_title="GIA - Capacitaciones", page_icon="🎓", layout="wide")

# ------------------ Helpers ------------------
def ensure_data_dir():
    """Asegurar que existe el directorio data"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(path, default):
    ensure_data_dir()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_csv(path):
    ensure_data_dir()
    if not os.path.exists(path):
        cols = [
            "timestamp","session_id","nombres","apellidos","cedula","correo","area",
            "evento","duracion_seg","observaciones"
        ]
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8")

def append_registro(**kwargs):
    ensure_csv(REG_FILE)
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": kwargs.get("session_id",""),
        "nombres": kwargs.get("nombres",""),
        "apellidos": kwargs.get("apellidos",""),
        "cedula": kwargs.get("cedula",""),
        "correo": kwargs.get("correo",""),
        "area": kwargs.get("area",""),
        "evento": kwargs.get("evento",""),
        "duracion_seg": kwargs.get("duracion_seg",""),
        "observaciones": kwargs.get("observaciones","")
    }
    df = pd.DataFrame([row])
    try:
        if os.path.getsize(REG_FILE) > 0:
            df.to_csv(REG_FILE, mode="a", header=False, index=False, encoding="utf-8")
        else:
            df.to_csv(REG_FILE, mode="a", header=True, index=False, encoding="utf-8")
    except Exception as e:
        st.error(f"Error guardando registro: {e}")

def get_registros_df():
    ensure_csv(REG_FILE)
    try:
        return pd.read_csv(REG_FILE, encoding="utf-8")
    except Exception:
        return pd.DataFrame()

def seconds_to_hms(s):
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
if "elapsed" not in st.session_state:
    st.session_state.elapsed = 0  # seconds
if "accumulated_time" not in st.session_state:
    st.session_state.accumulated_time = 0  # Para pausas

if "user" not in st.session_state:
    st.session_state.user = {}

if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = None

# ------------------ Sidebar ------------------
st.sidebar.title("🎓 GIA Capacitaciones")

# Mostrar info del usuario si está registrado
if st.session_state.user:
    st.sidebar.success(f"👤 {st.session_state.user.get('nombres', '')} {st.session_state.user.get('apellidos', '')}")
    st.sidebar.info(f"📍 Área: {st.session_state.user.get('area', '')}")
    st.sidebar.divider()

# Manejar redirección
if st.session_state.redirect_to:
    default_idx = ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"].index(st.session_state.redirect_to)
    st.session_state.redirect_to = None
else:
    default_idx = 0

mode = st.sidebar.radio("Navegación", ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"], index=default_idx)

# ------------------ Data ------------------
AREAS = load_json(AREAS_FILE, {})
NEWS = load_json(NEWS_FILE, [])

# Inicializar con datos de ejemplo si está vacío
if not AREAS:
    AREAS = {
        "Recursos Humanos": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://sharepoint.com/rrhh-video-1"
        ],
        "Ventas": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ],
        "Tecnología": [
            "https://sharepoint.com/tech-video-1"
        ]
    }
    save_json(AREAS_FILE, AREAS)

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
        for n in NEWS:
            with st.container():
                st.markdown(f"**{n.get('titulo','(sin título)')}**")
                st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
                if n.get("detalle"):
                    st.write(n.get("detalle",""))
                st.divider()

def page_registro():
    st.markdown("## 📝 Registro de Ingreso")
    
    if st.session_state.user:
        st.info("Ya te has registrado en esta sesión. Si deseas cambiar tus datos, recarga la página.")
        if st.button("Ir a Capacitaciones", type="primary"):
            st.session_state.redirect_to = "Capacitaciones"
            st.rerun()
        return
    
    col1, col2 = st.columns(2)
    with col1:
        nombres = st.text_input("Nombres*", placeholder="Pablo Andrés")
        cedula = st.text_input("Cédula*", placeholder="1234567890")
        area_options = list(AREAS.keys()) if AREAS else ["(Configurar en Admin)"]
        area = st.selectbox("Área*", options=area_options)
    with col2:
        apellidos = st.text_input("Apellidos*", placeholder="Granados Garay")
        correo = st.text_input("Correo*", placeholder="usuario@empresa.com")

    if st.button("🚀 Registrarme & Ir a Capacitaciones", type="primary"):
        if not (nombres and apellidos and cedula and correo and area and area in AREAS):
            st.error("⚠️ Completa todos los campos obligatorios y verifica el Área.")
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
            st.success("✅ Registro guardado. Redirigiendo a Capacitaciones...")
            time.sleep(1)
            st.session_state.redirect_to = "Capacitaciones"
            st.rerun()

def page_capacitaciones():
    st.markdown("## 🎥 Capacitaciones por Área")

    if not st.session_state.user:
        st.warning("⚠️ Primero realiza el **Registro** para personalizar tus capacitaciones.")
        if st.button("Ir a Registro"):
            st.session_state.redirect_to = "Registro"
            st.rerun()
        return

    area = st.session_state.user.get("area")
    st.write(f"**Área seleccionada:** {area}")
    urls = AREAS.get(area, [])

    if not urls:
        st.warning("No hay videos configurados para esta área. Solicita al administrador que los agregue en **Admin** → Áreas.")
    else:
        st.markdown("### 📹 Videos / Enlaces de capacitación:")
        for i, u in enumerate(urls, start=1):
            with st.container():
                # Para YouTube se puede usar st.video; para SharePoint mejor mostramos el enlace.
                if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()):
                    st.write(f"**Video {i}:**")
                    st.video(u)
                elif u.lower().endswith((".mp4",".webm",".mov")):
                    st.write(f"**Video {i}:**")
                    st.video(u)
                else:
                    st.markdown(f"**Enlace {i}:** [{u}]({u})")
                st.divider()

    # Cronómetro
    st.markdown("### ⏱️ Cronómetro de capacitación")

    # Calcular tiempo transcurrido
    current_elapsed = st.session_state.accumulated_time
    if st.session_state.timer_running and st.session_state.timer_start is not None:
        current_elapsed += int(time.time() - st.session_state.timer_start)

    col_timer, col_refresh = st.columns([3, 1])
    with col_timer:
        st.metric("Tiempo transcurrido", value=seconds_to_hms(current_elapsed))
    with col_refresh:
        if st.button("🔄 Actualizar"):
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
        if st.button("🏁 Finalizar capacitación", use_container_width=True, type="primary"):
            # Calcular tiempo final
            final_time = st.session_state.accumulated_time
            if st.session_state.timer_running and st.session_state.timer_start is not None:
                final_time += int(time.time() - st.session_state.timer_start)
            
            # Registrar
            append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="finalizacion",
                duracion_seg=final_time,
                observaciones="Capacitación finalizada"
            )
            
            # Reset timer
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.session_state.accumulated_time = 0
            
            st.success(f"✅ Se registró la finalización. Duración: {seconds_to_hms(final_time)}")
            st.balloons()

    st.info("💡 **Tip:** Puedes pausar y reanudar el cronómetro. El tiempo se acumula hasta que finalices.")

def page_noticias():
    st.markdown("## 📰 Noticias y Anuncios")
    if not NEWS:
        st.info("No hay noticias por el momento.")
        return
    
    for n in NEWS:
        with st.container():
            st.markdown(f"### {n.get('titulo','(sin título)')}")
            st.write(f"📅 **Fecha:** {n.get('fecha','') }")
            st.write(f"🧭 **Plataforma:** {n.get('plataforma','')}")
            if n.get("detalle"):
                st.write(n.get("detalle",""))
            st.divider()

def page_admin():
    st.markdown("## 🔐 Panel de Administración")
    pin = st.text_input("PIN de administrador", type="password", help="Configura GIA_ADMIN_PIN como variable de entorno para cambiarlo. (Por defecto: goleman123)")
    
    if pin != ADMIN_PIN:
        st.warning("⚠️ Ingresa el PIN correcto para continuar.")
        return

    st.success("✅ Acceso concedido.")

    tab1, tab2, tab3 = st.tabs(["📥 Registros", "🗓️ Noticias", "🏷️ Áreas"])

    with tab1:
        st.subheader("Registros de Usuarios")
        df = get_registros_df()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Registros", len(df))
            with col2:
                ingresos = len(df[df['evento'] == 'ingreso'])
                st.metric("Ingresos", ingresos)
            with col3:
                finalizaciones = len(df[df['evento'] == 'finalizacion'])
                st.metric("Finalizaciones", finalizaciones)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar CSV completo", 
                csv, 
                file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                type="primary"
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
            plataforma = st.text_input("Plataforma / Lugar*", placeholder="Zoom, Teams, Presencial, etc.")
            detalle = st.text_area("Detalle")
        
        if st.button("➕ Agregar noticia", type="primary"):
            if titulo and fecha and plataforma:
                news = load_json(NEWS_FILE, [])
                news.append({
                    "titulo": titulo, 
                    "fecha": fecha, 
                    "plataforma": plataforma, 
                    "detalle": detalle
                })
                save_json(NEWS_FILE, news)
                st.success("✅ Noticia agregada exitosamente!")
                st.rerun()
            else:
                st.error("⚠️ Completa los campos obligatorios.")
        
        st.divider()
        st.subheader("Noticias actuales")
        news_list = load_json(NEWS_FILE, [])
        if news_list:
            for idx, n in enumerate(news_list):
                with st.expander(f"{n.get('titulo', 'Sin título')} - {n.get('fecha', '')}"):
                    st.write(f"**Plataforma:** {n.get('plataforma', '')}")
                    st.write(f"**Detalle:** {n.get('detalle', 'N/A')}")
                    if st.button(f"🗑️ Eliminar", key=f"del_news_{idx}"):
                        news_list.pop(idx)
                        save_json(NEWS_FILE, news_list)
                        st.rerun()
        else:
            st.info("No hay noticias publicadas.")

    with tab3:
        st.subheader("Configuración de Áreas y Videos")
        st.write("Edita el JSON con el formato: `{\"Área\": [\"url1\", \"url2\", ...]}`")
        
        current = json.dumps(AREAS, ensure_ascii=False, indent=2)
        edited = st.text_area("JSON de áreas y videos", value=current, height=300)
        
        if st.button("💾 Guardar áreas", type="primary"):
            try:
                new_data = json.loads(edited)
                save_json(AREAS_FILE, new_data)
                st.success("✅ Áreas actualizadas exitosamente!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ JSON inválido: {e}")

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
