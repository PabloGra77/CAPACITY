# app.py
# -------------------------------------------------------------
# Capacitaciones App (Streamlit)
# Registro de ingreso, videos por área (URLs/SharePoint),
# cronómetro de tiempo de capacitación y exportes CSV/Excel/PDF.
# -------------------------------------------------------------

import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict

import pandas as pd
import streamlit as st

# --- Opcional para PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    HAS_PDF = True
except Exception:
    HAS_PDF = False

st.set_page_config(page_title="Capacitaciones Goleman / Demo", page_icon="🎓", layout="wide")

# =============================================================
# CONFIGURACIÓN (edita esto según tus áreas y videos)
# =============================================================
# 1) Mapa de Áreas -> Lista de URLs de videos (pueden ser MP4 directos,
#    enlaces de SharePoint/OneDrive o YouTube). st.video acepta URLs.
#    Ejemplos de SharePoint al final del archivo (sección de notas).
AREAS_VIDEOS: Dict[str, List[str]] = {
    "Tecnología": [
        # Reemplaza con tus enlaces reales
        "https://www.w3schools.com/html/mov_bbb.mp4",
    ],
    "Talento Humano": [
        "https://www.w3schools.com/html/movie.mp4",
    ],
    "Atención al Usuario": [
        "https://www.w3schools.com/html/mov_bbb.mp4",
    ],
}

# 2) Título de la app y banner opcional
APP_TITLE = "Plataforma de Capacitaciones"
BANNER = None  # URL a una imagen si deseas mostrar un banner superior

# 3) Seguridad mínima para descargar reportes (simple "clave" en memoria)
REPORTE_PIN = st.secrets.get("REPORTE_PIN", "1234")  # cambia en .streamlit/secrets.toml

# 4) Nombre del archivo de base de datos (persistencia local en Streamlit Cloud es efímera)
DB_PATH = "capacitaciones.db"

# =============================================================
# DB: inicialización y helpers
# =============================================================
@st.cache_resource(show_spinner=False)
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_ingreso TEXT NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            cedula TEXT NOT NULL,
            correo TEXT NOT NULL,
            area TEXT NOT NULL,
            ts_inicio_cap TEXT,
            ts_fin_cap TEXT,
            segundos_cap INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_publicacion TEXT NOT NULL,
            titulo TEXT NOT NULL,
            cuerpo TEXT
        )
        """
    )
    conn.commit()
    return conn


def insertar_registro(conn, datos: dict) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO registros (
            ts_ingreso, nombres, apellidos, cedula, correo, area, ts_inicio_cap, ts_fin_cap, segundos_cap
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos["ts_ingreso"], datos["nombres"], datos["apellidos"], datos["cedula"],
            datos["correo"], datos["area"], None, None, 0
        ),
    )
    conn.commit()
    return cur.lastrowid


def iniciar_capacitacion(conn, registro_id: int):
    ts = datetime.utcnow().isoformat()
    conn.execute("UPDATE registros SET ts_inicio_cap=? WHERE id=?", (ts, registro_id))
    conn.commit()


def finalizar_capacitacion(conn, registro_id: int):
    # Calcula segundos entre inicio y ahora y acumula (por si hay múltiples sesiones)
    cur = conn.cursor()
    cur.execute("SELECT ts_inicio_cap, segundos_cap FROM registros WHERE id=?", (registro_id,))
    row = cur.fetchone()
    if not row:
        return
    ts_inicio, acumulado = row
    ahora_iso = datetime.utcnow().isoformat()
    segundos = 0
    if ts_inicio:
        try:
            segundos = int((datetime.fromisoformat(ahora_iso) - datetime.fromisoformat(ts_inicio)).total_seconds())
        except Exception:
            segundos = 0
    total = int(acumulado or 0) + max(0, segundos)
    conn.execute(
        "UPDATE registros SET ts_fin_cap=?, segundos_cap=?, ts_inicio_cap=NULL WHERE id=?",
        (ahora_iso, total, registro_id),
    )
    conn.commit()


def get_registros_df(conn, fecha_desde: str = None, fecha_hasta: str = None):
    q = "SELECT id, ts_ingreso, nombres, apellidos, cedula, correo, area, ts_inicio_cap, ts_fin_cap, segundos_cap FROM registros"
    params = []
    filtros = []
    if fecha_desde:
        filtros.append("datetime(ts_ingreso) >= datetime(?)")
        params.append(fecha_desde)
    if fecha_hasta:
        filtros.append("datetime(ts_ingreso) <= datetime(?)")
        params.append(fecha_hasta)
    if filtros:
        q += " WHERE " + " AND ".join(filtros)
    q += " ORDER BY ts_ingreso DESC"
    df = pd.read_sql_query(q, get_conn(), params=params)
    # Columnas amigables
    if not df.empty:
        df["minutos_cap"] = (df["segundos_cap"].fillna(0) / 60).round(1)
    return df


def publicar_noticia(conn, titulo: str, cuerpo: str):
    conn.execute(
        "INSERT INTO noticias (ts_publicacion, titulo, cuerpo) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), titulo, cuerpo),
    )
    conn.commit()


def listar_noticias(conn):
    return pd.read_sql_query(
        "SELECT ts_publicacion, titulo, cuerpo FROM noticias ORDER BY ts_publicacion DESC",
        conn,
    )


# =============================================================
# UTILIDADES UI
# =============================================================

def ui_banner():
    if BANNER:
        st.image(BANNER, use_column_width=True)


def ui_titulo():
    st.markdown(f"## {APP_TITLE}")


# =============================================================
# SIDEBAR: navegación simple
# =============================================================
PAGES = [
    "Ingreso",
    "Capacitación",
    "Noticias",
    "Reportes",
]

with st.sidebar:
    st.markdown("### Navegación")
    page = st.radio("Ir a", options=PAGES)
    st.markdown("---")
    st.markdown("**Sesión**")
    if "registro_id" in st.session_state:
        st.success(f"Sesión activa: ID {st.session_state['registro_id']}")
    else:
        st.info("Sin sesión de capacitación activa.")


# =============================================================
# PÁGINA: Ingreso (registro de evidencia)
# =============================================================
if page == "Ingreso":
    ui_banner(); ui_titulo()
    st.markdown("**Registra tus datos para ingresar a la plataforma de capacitaciones.**\nNo se crean cuentas; solo guardamos evidencia del ingreso.")

    with st.form("form_ingreso", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nombres = st.text_input("Nombres", placeholder="Juan Camilo", max_chars=80)
            cedula = st.text_input("Cédula", placeholder="1234567890", max_chars=30)
            area = st.selectbox("Área", options=list(AREAS_VIDEOS.keys()))
        with col2:
            apellidos = st.text_input("Apellidos", placeholder="Pérez Gómez", max_chars=80)
            correo = st.text_input("Correo", placeholder="usuario@empresa.com", max_chars=120)
        submitted = st.form_submit_button("Ingresar y registrar evidencia ✅")

    if submitted:
        if not (nombres and apellidos and cedula and correo and area):
            st.error("Por favor completa todos los campos.")
        else:
            conn = get_conn()
            registro_id = insertar_registro(
                conn,
                {
                    "ts_ingreso": datetime.utcnow().isoformat(),
                    "nombres": nombres.strip(),
                    "apellidos": apellidos.strip(),
                    "cedula": cedula.strip(),
                    "correo": correo.strip(),
                    "area": area,
                },
            )
            st.session_state["registro_id"] = registro_id
            st.session_state["area"] = area
            st.session_state["nombres"] = nombres
            st.session_state["apellidos"] = apellidos
            st.session_state["cronometro_activo"] = False
            st.success(f"Ingreso registrado (ID #{registro_id}). Ahora ve a la pestaña **Capacitación**.")


# =============================================================
# PÁGINA: Capacitación (videos + cronómetro)
# =============================================================
if page == "Capacitación":
    ui_banner(); ui_titulo()

    if "registro_id" not in st.session_state:
        st.warning("Primero registra tu ingreso en la pestaña **Ingreso**.")
    else:
        colA, colB = st.columns([2, 1])
        with colA:
            st.markdown("### Videos de tu área")
            area_sel = st.selectbox("Área", options=list(AREAS_VIDEOS.keys()), index=list(AREAS_VIDEOS.keys()).index(st.session_state.get("area", list(AREAS_VIDEOS.keys())[0])))
            st.session_state["area"] = area_sel

            videos = AREAS_VIDEOS.get(area_sel, [])
            if not videos:
                st.info("No hay videos configurados para esta área aún.")
            else:
                for i, url in enumerate(videos, start=1):
                    st.markdown(f"**Video {i}**")
                    st.video(url)

        with colB:
            st.markdown("### Cronómetro")
            st.caption("El cronómetro mide tu tiempo en esta sección. Usa **Iniciar** y **Finalizar**.")

            if "cronometro_segundos_acum" not in st.session_state:
                st.session_state["cronometro_segundos_acum"] = 0
            if "cronometro_inicio" not in st.session_state:
                st.session_state["cronometro_inicio"] = None

            def _tick():
                if st.session_state.get("cronometro_activo") and st.session_state.get("cronometro_inicio"):
                    delta = (datetime.utcnow() - st.session_state["cronometro_inicio"]).total_seconds()
                    st.session_state["cronometro_segundos_display"] = int(st.session_state.get("cronometro_segundos_acum", 0) + max(0, delta))
                else:
                    st.session_state["cronometro_segundos_display"] = int(st.session_state.get("cronometro_segundos_acum", 0))

            # Autorefresco ligero para ver correr el tiempo
            st_autoref = st.empty()
            st_autoref.experimental_rerun = False
            st.autorefresh(interval=1000, key="tick")
            _tick()

            total_secs = int(st.session_state.get("cronometro_segundos_display", 0))
            mins = total_secs // 60
            secs = total_secs % 60
            st.metric("Tiempo acumulado", f"{mins:02d}:{secs:02d}")

            col1, col2 = st.columns(2)
            if col1.button("▶️ Iniciar", use_container_width=True):
                if not st.session_state.get("cronometro_activo"):
                    st.session_state["cronometro_activo"] = True
                    st.session_state["cronometro_inicio"] = datetime.utcnow()
                    # Marca inicio en DB si aún no hay
                    iniciar_capacitacion(get_conn(), st.session_state["registro_id"])

            if col2.button("⏹ Finalizar", type="primary", use_container_width=True):
                if st.session_state.get("cronometro_activo") and st.session_state.get("cronometro_inicio"):
                    delta = (datetime.utcnow() - st.session_state["cronometro_inicio"]).total_seconds()
                    st.session_state["cronometro_segundos_acum"] += int(max(0, delta))
                st.session_state["cronometro_activo"] = False
                st.session_state["cronometro_inicio"] = None
                # Persistir en DB
                conn = get_conn()
                finalizar_capacitacion(conn, st.session_state["registro_id"])
                st.success("Tiempo registrado y guardado.")

            st.caption("Nota: para un conteo 'tiempo efectivo' más estricto (pausar si cambias de pestaña/ventana), se puede añadir un componente JS con Page Visibility API. Este MVP usa un cronómetro manual confiable.")


# =============================================================
# PÁGINA: Noticias
# =============================================================
if page == "Noticias":
    ui_banner(); ui_titulo()
    st.markdown("### Publicar anuncio")
    with st.form("form_noticia"):
        titulo = st.text_input("Título", placeholder="Capacitación de seguridad informática — 12/11 3:00 p.m. — vía Teams")
        cuerpo = st.text_area("Cuerpo (opcional)", placeholder="Ingresa con el enlace: ...")
        pub = st.form_submit_button("Publicar")
    if pub and titulo:
        publicar_noticia(get_conn(), titulo.strip(), (cuerpo or "").strip())
        st.success("Noticia publicada.")

    st.markdown("### Anuncios recientes")
    df_n = listar_noticias(get_conn())
    if df_n.empty:
        st.info("Aún no hay anuncios publicados.")
    else:
        for _, r in df_n.iterrows():
            st.info(f"**{r['titulo']}**\n\n{r['cuerpo'] or ''}\n\n_Publicado: {r['ts_publicacion']}_")


# =============================================================
# PÁGINA: Reportes (descargas CSV/Excel/PDF)
# =============================================================
if page == "Reportes":
    ui_banner(); ui_titulo()
    st.markdown("### Descarga de registros")
    pin = st.text_input("PIN de descarga", type="password")

    colf1, colf2 = st.columns(2)
    with colf1:
        f_desde = st.date_input("Desde", value=None)
    with colf2:
        f_hasta = st.date_input("Hasta", value=None)

    fecha_desde = f"{f_desde} 00:00:00" if f_desde else None
    fecha_hasta = f"{f_hasta} 23:59:59" if f_hasta else None

    if st.button("Generar reporte"):
        if pin != REPORTE_PIN:
            st.error("PIN incorrecto.")
        else:
            df = get_registros_df(get_conn(), fecha_desde, fecha_hasta)
            if df.empty:
                st.warning("No hay registros en el rango seleccionado.")
            else:
                st.dataframe(df, use_container_width=True)

                # CSV
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Descargar CSV", data=csv, file_name="reporte_capacitaciones.csv", mime="text/csv")

                # Excel
                bio = BytesIO()
                with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Registros")
                    ws = writer.sheets["Registros"]
                    for i, col in enumerate(df.columns):
                        ws.set_column(i, i, min(30, max(12, int(df[col].astype(str).str.len().mean() + 4))))
                st.download_button(
                    "⬇️ Descargar Excel",
                    data=bio.getvalue(),
                    file_name="reporte_capacitaciones.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                # PDF (si reportlab instalado)
                if HAS_PDF:
                    pdf_buffer = BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                    styles = getSampleStyleSheet()
                    story = [Paragraph("Reporte de Capacitaciones", styles['Title']), Spacer(1, 12)]

                    # Encabezado simple
                    filtros = f"Rango: {fecha_desde or '-'} a {fecha_hasta or '-'}"
                    story.append(Paragraph(filtros, styles['Normal']))
                    story.append(Spacer(1, 12))

                    # Tabla
                    data = [list(df.columns)] + df.values.tolist()
                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ]))
                    story.append(table)

                    doc.build(story)
                    st.download_button(
                        "⬇️ Descargar PDF",
                        data=pdf_buffer.getvalue(),
                        file_name="reporte_capacitaciones.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.info("Para exportar a PDF, agrega `reportlab` a requirements.txt.")

# =============================================================
# NOTAS y buenas prácticas para SharePoint / OneDrive
# =============================================================
# - Para usar videos de SharePoint/OneDrive con st.video, lo más estable es un enlace directo a MP4
#   o un enlace de compartición que permita acceso anónimo (si el público es externo) o autenticado
#   (si todos los usuarios están en la organización). Ejemplos:
#
#   1) Enlace de compartición público (si tu política lo permite) con parámetro de descarga:
#      https://<tu-tenant>.sharepoint.com/:v:/r/sites/<sitio>/Shared%20Documents/<carpeta>/video.mp4?download=1
#
#   2) Enlace de OneDrive (similar) con `download=1`.
#
# - Si prefieres el reproductor embebido de Microsoft, puedes usar st.components.v1.iframe(embebido_url, ...)
#   pero st.video suele bastar si la URL devuelve un stream compatible.
#
# - Verifica permisos: si los usuarios no pueden reproducir, revisa que el link sea accesible
#   para quienes ingresan (mismo dominio/tenant o vínculo de invitado).

# =============================================================
# DESPLIEGUE recomendado
# =============================================================
# Opción A) Streamlit Cloud (rápido y sin servidores):
#   1. Sube este repo a GitHub con app.py y requirements.txt
#   2. Crea la app en https://share.streamlit.io/ apuntando al repo
#   3. En "Secrets" agrega REPORTE_PIN si quieres cambiar el PIN de Reportes
#   4. DB SQLite es local y efímera. Para persistencia duradera, considera:
#      - Google Sheets (gspread) o Airtable
#      - Supabase / Postgres gestionado
#      - Azure/Heroku Postgres
#
# Opción B) Docker + VM/Contenedor (empresa):
#   - Construye una imagen con Python 3.11, instala requirements.txt
#   - Ejecuta: streamlit run app.py --server.port 8501 --server.enableCORS=false
#
# Requisitos mínimos:
#   - Python 3.10+ (recomendado 3.11)
#   - Paquetes: streamlit, pandas, xlsxwriter, (opcional) reportlab
#
# Extensiones futuras:
#   - Autenticación mínima para crear noticias (PIN de editor)
#   - Mapeo de videos configurable vía CSV subido por admin
#   - Componente JS para pausar cronómetro al cambiar de pestaña (Page Visibility API)

# =============================================================
# FIN app.py


# requirements.txt
# streamlit==1.38.0
# pandas==2.2.2
# XlsxWriter==3.2.0
# reportlab==4.2.5  # opcional para exportar a PDF
