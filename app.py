
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
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_csv(path):
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
    df.to_csv(REG_FILE, mode="a", header=not os.path.getsize(REG_FILE), index=False, encoding="utf-8")

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

if "user" not in st.session_state:
    st.session_state.user = {}

# ------------------ Sidebar ------------------
st.sidebar.title("GIA Capacitaciones")
mode = st.sidebar.radio("Navegación", ["Inicio", "Registro", "Capacitaciones", "Noticias", "Admin"], index=0)

# ------------------ Data ------------------
AREAS = load_json(AREAS_FILE, {})
NEWS = load_json(NEWS_FILE, [])

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
            with st.container(border=True):
                st.write(f"**{n.get('titulo','(sin título)')}**")
                st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
                st.write(n.get("detalle",""))

def page_registro():
    st.markdown("## 📝 Registro de Ingreso")
    with st.form("registro_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nombres = st.text_input("Nombres*", placeholder="Pablo Andrés")
            cedula = st.text_input("Cédula*", placeholder="1234567890")
            area = st.selectbox("Área*", options=list(AREAS.keys()) if AREAS else ["(Configurar en Admin)"])
        with col2:
            apellidos = st.text_input("Apellidos*", placeholder="Granados Garay")
            correo = st.text_input("Correo*", placeholder="usuario@empresa.com")

        submitted = st.form_submit_button("Registrarme & Ir a Capacitaciones", type="primary")
        if submitted:
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
                append_registro(
                    session_id=st.session_state.session_id,
                    **st.session_state.user,
                    evento="ingreso",
                    duracion_seg="",
                    observaciones="Registro inicial"
                )
                st.success("Registro guardado. Redirigiendo a Capacitaciones...")
                st.session_state._go_to = "Capacitaciones"

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
            # Para YouTube se puede usar st.video; para SharePoint mejor mostramos el enlace.
            if ("youtube.com" in u.lower()) or ("youtu.be" in u.lower()) or u.lower().endswith((".mp4",".webm",".mov")):
                st.write(f"Video {i}:")
                st.video(u)
            else:
                st.markdown(f"- Enlace {i}: {u}")

    # Cronómetro
    st.divider()
    st.markdown("### ⏱️ Cronómetro de capacitación")

    # Mostrar tiempo transcurrido
    if st.session_state.timer_running and st.session_state.timer_start is not None:
        st.session_state.elapsed = int(time.time() - st.session_state.timer_start)

    st.metric("Tiempo transcurrido", value=seconds_to_hms(st.session_state.elapsed))

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("Iniciar", disabled=st.session_state.timer_running):
            st.session_state.timer_running = True
            st.session_state.timer_start = time.time()
            st.toast("Cronómetro iniciado", icon="⏱️")
    with colB:
        if st.button("Pausar", disabled=not st.session_state.timer_running):
            st.session_state.timer_running = False
            if st.session_state.timer_start is not None:
                st.session_state.elapsed = int(time.time() - st.session_state.timer_start)
            st.toast("Cronómetro pausado", icon="⏸️")
    with colC:
        if st.button("Finalizar capacitación"):
            # Detener y registrar
            if st.session_state.timer_running and st.session_state.timer_start is not None:
                st.session_state.elapsed = int(time.time() - st.session_state.timer_start)
                st.session_state.timer_running = False
                st.session_state.timer_start = None
            append_registro(
                session_id=st.session_state.session_id,
                **st.session_state.user,
                evento="finalizacion",
                duracion_seg=st.session_state.elapsed,
                observaciones="Capacitación finalizada"
            )
            st.success(f"Se registró la finalización. Duración: {seconds_to_hms(st.session_state.elapsed)}")
            st.balloons()

def page_noticias():
    st.markdown("## 📰 Noticias y Anuncios")
    if not NEWS:
        st.info("No hay noticias por el momento.")
        return
    for n in NEWS:
        with st.container(border=True):
            st.write(f"**{n.get('titulo','(sin título)')}**")
            st.write(f"📅 {n.get('fecha','') } · 🧭 {n.get('plataforma','')}")
            st.write(n.get("detalle",""))

def page_admin():
    st.markdown("## 🔐 Admin")
    pin = st.text_input("PIN de administrador", type="password", help="Configura GIA_ADMIN_PIN como variable de entorno para cambiarlo.")
    if pin != ADMIN_PIN:
        st.warning("Ingresa el PIN correcto para continuar.")
        return

    st.success("Acceso concedido.")

    with st.expander("📥 Descarga de registros"):
        df = get_registros_df()
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, file_name="registros.csv", mime="text/csv")

    with st.expander("🗓️ Gestionar noticias"):
        with st.form("news_form"):
            titulo = st.text_input("Título")
            fecha = st.text_input("Fecha (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            plataforma = st.text_input("Plataforma / Lugar")
            detalle = st.text_area("Detalle")
            add_news = st.form_submit_button("Agregar noticia")
        if add_news and titulo:
            news = load_json(NEWS_FILE, [])
            news.append({"titulo": titulo, "fecha": fecha, "plataforma": plataforma, "detalle": detalle})
            save_json(NEWS_FILE, news)
            st.success("Noticia agregada. Recarga la página para ver los cambios.")

    with st.expander("🏷️ Áreas y videos (JSON)"):
        current = json.dumps(AREAS, ensure_ascii=False, indent=2)
        edited = st.text_area("Edita el JSON de áreas → videos", value=current, height=300)
        if st.button("Guardar áreas"):
            try:
                new_data = json.loads(edited)
                save_json(AREAS_FILE, new_data)
                st.success("Áreas actualizadas. Recarga la página para aplicar cambios.")
            except Exception as e:
                st.error(f"JSON inválido: {e}")

# ------------------ Router ------------------
if " _go_to" in st.session_state:
    # internal redirect after registro
    mode = st.session_state.pop("_go_to")

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
