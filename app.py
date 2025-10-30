import os, json, time, uuid
from datetime import datetime
import pandas as pd
import streamlit as st

# Rutas de archivos - usar ruta relativa simple
DATA_DIR = "data"
AREAS_FILE = os.path.join(DATA_DIR, "areas.json")
NEWS_FILE = os.path.join(DATA_DIR, "news.json")
REG_FILE = os.path.join(DATA_DIR, "registros.csv")

ADMIN_PIN = os.getenv("GIA_ADMIN_PIN", "goleman123")

st.set_page_config(page_title="GIA - Capacitaciones", page_icon="🎓", layout="wide")

# ------------------ Helpers ------------------
def ensure_data_dir():
    """Asegurar que el directorio data existe"""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except Exception as e:
            st.error(f"No se pudo crear el directorio data: {e}")

def load_json(path, default):
    """Cargar archivo JSON"""
    ensure_data_dir()
    try:
        # Si es un directorio en lugar de archivo, eliminarlo
        if os.path.exists(path) and os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.sidebar.warning(f"No se pudo cargar {os.path.basename(path)}")
    return default

def save_json(path, data):
    """Guardar archivo JSON"""
    ensure_data_dir()
    try:
        # Si el path existe y es un directorio, eliminarlo
        if os.path.exists(path) and os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error guardando {path}: {e}")
        return False

def ensure_csv(path):
    """Asegurar que el archivo CSV existe con las columnas correctas"""
    ensure_data_dir()
    if not os.path.exists(path):
        try:
            cols = [
                "timestamp","session_id","nombres","apellidos","cedula","correo","area",
                "evento","duracion_seg","observaciones"
            ]
            pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8")
        except Exception as e:
            st.error(f"Error creando CSV: {e}")

def append_registro(**kwargs):
    """Agregar un registro al CSV"""
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
    try:
        df = pd.DataFrame([row])
        if os.path.exists(REG_FILE) and os.path.getsize(REG_FILE) > 0:
            df.to_csv(REG_FILE, mode="a", header=False, index=False, encoding="utf-8")
        else:
            df.to_csv(REG_FILE, mode="w", header=True, index=False, encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Error guardando registro: {e}")
        return False

def get_registros_df():
    """Obtener registros como DataFrame"""
    ensure_csv(REG_FILE)
    try:
        if os.path.exists(REG_FILE) and os.path.getsize(REG_FILE) > 0:
            return pd.read_csv(REG_FILE, encoding="utf-8")
    except Exception as e:
        st.warning(f"Error leyendo registros: {e}")
    
    # Retornar DataFrame vacío con las columnas correctas
    cols = [
        "timestamp","session_id","nombres","apellidos","cedula","correo","area",
        "evento","duracion_seg","observaciones"
    ]
    return pd.DataFrame(columns=cols)

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
st.sidebar.title("GIA Capacitaciones")

if st.session_state.user:
    st.sidebar.success(f"👤 {st.session_state.user.get('nombres', '')} {st.session_state.user.get('apellidos', '')}")
    st.sidebar.info(f"📍 {st.session_state.user.get('area', '')}")
    st.sidebar.divider()

mode = st.sidebar.radio("Navegación", ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"], index=0)

# ------------------ Data ------------------
ensure_data_dir()

AREAS = load_json(AREAS_FILE, {})
NEWS = load_json(NEWS_FILE, [])

# Inicializar áreas de ejemplo si no existen
if not AREAS:
    default_areas = {
        "Recursos Humanos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "Ventas": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "Tecnología": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    }
    if save_json(AREAS_FILE, default_areas):
        AREAS = default_areas
        st.sidebar.success("✅ Áreas inicializadas correctamente")
    else:
        st.sidebar.warning("⚠️ No se pudieron crear las áreas. Por favor, crea la carpeta 'data' manualmente.")

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
                st.write(f"**{n.get('titulo','(sin título)')}**")
                st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
                st.write(n.get("detalle",""))
                st.divider()

def page_registro():
    st.markdown("## 📝 Registro de Ingreso")
    
    if st.session_state.user:
        st.info("Ya te has registrado en esta sesión. Si deseas cambiar tus datos, recarga la página.")
        if st.button("Ir a Capacitaciones", type="primary"):
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
            st.error("Completa todos los campos obligatorios y verifica el Área.")
        else:
            st.session_state.user = {
                "nombres": nombres.strip(),
                "apellidos": apellidos.strip(),
                "cedula": cedula.strip(),
                "correo": correo.strip(),
                "area": area.strip()
            }
            if append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="ingreso",
                duracion_seg="",
                observaciones="Registro inicial"
            ):
                st.success("Registro guardado. Redirigiendo a Capacitaciones...")
                time.sleep(1)
                st.rerun()

def page_capacitaciones():
    st.markdown("## 🎥 Capacitaciones por Área")

    if not st.session_state.user:
        st.info("Primero realiza el **Registro** para personalizar tus capacitaciones.")
        return

    area = st.session_state.user.get("area")
    st.write(f"**Área seleccionada:** {area}")
    urls = AREAS.get(area, [])

    if not urls:
        st.warning("No hay videos configurados para esta área. Solicita al administrador que los agregue en **Admin** → Áreas.")
    else:
        st.write("**Videos / Enlaces de capacitación**:")
        for i, u in enumerate(urls, start=1):
            if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()) or u.lower().endswith((".mp4",".webm",".mov")):
                st.write(f"Video {i}:")
                st.video(u)
            else:
                st.markdown(f"- Enlace {i}: [{u}]({u})")

    # Cronómetro
    st.divider()
    st.markdown("### ⏱️ Cronómetro de capacitación")

    # Calcular tiempo transcurrido
    current_elapsed = st.session_state.accumulated_time
    if st.session_state.timer_running and st.session_state.timer_start is not None:
        current_elapsed += int(time.time() - st.session_state.timer_start)

    st.metric("Tiempo transcurrido", value=seconds_to_hms(current_elapsed))

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("Iniciar", disabled=st.session_state.timer_running):
            st.session_state.timer_running = True
            st.session_state.timer_start = time.time()
            st.toast("Cronómetro iniciado", icon="⏱️")
            st.rerun()
    with colB:
        if st.button("Pausar", disabled=not st.session_state.timer_running):
            if st.session_state.timer_start is not None:
                st.session_state.accumulated_time += int(time.time() - st.session_state.timer_start)
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.toast("Cronómetro pausado", icon="⏸️")
            st.rerun()
    with colC:
        if st.button("Finalizar capacitación"):
            # Calcular tiempo final
            final_time = st.session_state.accumulated_time
            if st.session_state.timer_running and st.session_state.timer_start is not None:
                final_time += int(time.time() - st.session_state.timer_start)
            
            if append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="finalizacion",
                duracion_seg=final_time,
                observaciones="Capacitación finalizada"
            ):
                # Reset
                st.session_state.timer_running = False
                st.session_state.timer_start = None
                st.session_state.accumulated_time = 0
                
                st.success(f"Se registró la finalización. Duración: {seconds_to_hms(final_time)}")
                st.balloons()

def page_noticias():
    st.markdown("## 📰 Noticias y Anuncios")
    if not NEWS:
        st.info("No hay noticias por el momento.")
        return
    for n in NEWS:
        with st.container():
            st.write(f"**{n.get('titulo','(sin título)')}**")
            st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
            st.write(n.get("detalle",""))
            st.divider()

def page_admin():
    st.markdown("## 🔐 Admin")
    pin = st.text_input("PIN de administrador", type="password", help="Configura GIA_ADMIN_PIN como variable de entorno para cambiarlo.")
    if pin != ADMIN_PIN:
        st.warning("Ingresa el PIN correcto para continuar.")
        return

    st.success("Acceso concedido.")

    with st.expander("📥 Descarga de registros", expanded=True):
        df = get_registros_df()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar CSV", csv, file_name=f"registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
        else:
            st.info("No hay registros todavía.")

    with st.expander("🗓️ Gestionar noticias"):
        titulo = st.text_input("Título")
        fecha = st.text_input("Fecha (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        plataforma = st.text_input("Plataforma / Lugar")
        detalle = st.text_area("Detalle")
        if st.button("Agregar noticia") and titulo:
            news = load_json(NEWS_FILE, [])
            news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
            if save_json(NEWS_FILE, news):
                st.success("Noticia agregada. Recarga la página para ver los cambios.")

    with st.expander("🏷️ Áreas y videos (JSON)"):
        current = json.dumps(AREAS, ensure_ascii=False, indent=2)
        edited = st.text_area("Edita el JSON de áreas → videos", value=current, height=300)
        if st.button("Guardar áreas"):
            try:
                new_data = json.loads(edited)
                if save_json(AREAS_FILE, new_data):
                    st.success("Áreas actualizadas. Recarga la página para aplicar cambios.")
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
