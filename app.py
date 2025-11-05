import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import unicodedata
import time as time_module

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(
    page_title="GIA - Sistema SLA",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes
OFFSET_HOURS = 5.0
WORK_SCHEDULE = {
    0: [(time(7,0), time(17,0))],
    1: [(time(7,0), time(17,0))],
    2: [(time(7,0), time(17,0))],
    3: [(time(7,0), time(17,0))],
    4: [(time(7,0), time(16,0))],
    5: [(time(8,0), time(13,0))],
    6: []
}

SLA_HOURS = {
    "muy alta": 4,
    "alta": 8,
    "media": 16,
    "baja": 32,
    "muy baja": 2/60
}

# ==========================================
# ESTILOS CSS MODERNOS
# ==========================================
st.markdown("""
<style>
    /* Tema principal */
    :root {
        --primary: #2E86DE;
        --success: #10AC84;
        --warning: #F79F1F;
        --danger: #EE5A6F;
        --dark: #1E272E;
        --light: #F8F9FA;
    }
    
    /* Fondo */
    .stApp {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
    }
    
    /* Tarjetas métricas */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: 900;
        line-height: 1;
        margin: 12px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 14px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Encabezados */
    h1, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Botones personalizados */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* Tablas */
    .dataframe {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def norm(s: str) -> str:
    if pd.isna(s) or s is None:
        return ""
    s = str(s)
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) 
                if unicodedata.category(ch) != "Mn")
    return s.lower().strip()

def to_timestamp(fecha_str, offset=OFFSET_HOURS):
    if pd.isna(fecha_str):
        return pd.NaT
    try:
        dt = pd.to_datetime(fecha_str, errors='coerce', dayfirst=True)
        if pd.isna(dt):
            return pd.NaT
        return dt - timedelta(hours=offset)
    except:
        return pd.NaT

def business_hours_between(start: datetime, end: datetime) -> float:
    if pd.isna(start) or pd.isna(end) or end <= start:
        return 0.0
    
    total_seconds = 0.0
    current = start
    
    for _ in range(400):
        current_date = current.date()
        weekday = current.weekday()
        
        if weekday not in WORK_SCHEDULE or not WORK_SCHEDULE[weekday]:
            next_day = datetime.combine(current_date + timedelta(days=1), time(0, 0))
            if next_day >= end:
                break
            current = next_day
            continue
        
        for (start_time, end_time) in WORK_SCHEDULE[weekday]:
            block_start = datetime.combine(current_date, start_time)
            block_end = datetime.combine(current_date, end_time)
            
            actual_start = max(current, block_start)
            actual_end = min(end, block_end)
            
            if actual_end > actual_start:
                total_seconds += (actual_end - actual_start).total_seconds()
        
        next_day = datetime.combine(current_date + timedelta(days=1), time(0, 0))
        if next_day >= end:
            break
        current = next_day
    
    return total_seconds / 3600.0

def get_sla_hours(priority: str) -> float:
    if pd.isna(priority):
        return 8.0
    
    priority_norm = norm(priority)
    
    if "muy baja" in priority_norm or "muybaja" in priority_norm:
        return 2/60
    elif "muy alta" in priority_norm or "muyalta" in priority_norm:
        return 4
    elif "alta" in priority_norm:
        return 8
    elif "media" in priority_norm:
        return 16
    elif "baja" in priority_norm:
        return 32
    
    return 8.0

def is_resolved(estado: str) -> bool:
    estado_norm = norm(estado)
    return "resuel" in estado_norm or "cerr" in estado_norm or "solucion" in estado_norm

def procesar_datos(df: pd.DataFrame):
    df["Fecha Apertura"] = df["Fecha de apertura"].apply(to_timestamp)
    df["Resuelto"] = df["Estados"].apply(is_resolved)
    
    df["Fecha Cierre"] = df.apply(
        lambda r: to_timestamp(r["Última modificación"]) if r["Resuelto"] else pd.NaT,
        axis=1
    )
    
    def calc_horas(row):
        if pd.isna(row["Fecha Apertura"]):
            return 0.0
        
        if row["Resuelto"] and pd.notna(row["Fecha Cierre"]):
            end_date = row["Fecha Cierre"]
        else:
            end_date = datetime.now()
        
        return business_hours_between(row["Fecha Apertura"], end_date)
    
    df["Horas Hábiles"] = df.apply(calc_horas, axis=1)
    df["Minutos Hábiles"] = df["Horas Hábiles"] * 60
    df["SLA Límite (h)"] = df["Prioridad"].apply(get_sla_hours)
    df["SLA Límite (min)"] = df["SLA Límite (h)"] * 60
    
    def estado_sla(row):
        if not row["Resuelto"]:
            if row["Horas Hábiles"] > row["SLA Límite (h)"]:
                return "Abierto (Tardío)"
            return "Abierto"
        else:
            if row["Horas Hábiles"] <= row["SLA Límite (h)"]:
                return "Cumplido"
            return "Tardío"
    
    df["Estado SLA"] = df.apply(estado_sla, axis=1)
    df["Es Tardío"] = df["Estado SLA"].str.contains("Tardío")
    
    return df

def generar_resumen(df: pd.DataFrame, col_tecnico: str) -> pd.DataFrame:
    resumen = df.groupby(col_tecnico).agg(
        Asignados=("ID", "count"),
        Resueltos=("Resuelto", "sum"),
        Tardíos=("Es Tardío", "sum")
    ).reset_index()
    
    def calc_sla_pct(row):
        if row["Resueltos"] == 0:
            return 0.0
        cumplidos = row["Resueltos"] - row["Tardíos"]
        return (cumplidos / row["Resueltos"]) * 100
    
    resumen["SLA (%)"] = resumen.apply(calc_sla_pct, axis=1)
    
    return resumen

def crear_tarjeta_metrica(label, value, icon="📊"):
    return f"""
    <div class='metric-card'>
        <div class='metric-label'>{icon} {label}</div>
        <div class='metric-value'>{value}</div>
    </div>
    """

# ==========================================
# SIDEBAR - CONFIGURACIÓN
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    
    # Selector de modo
    modo = st.radio(
        "Modo de visualización",
        ["📊 Dashboard Completo", "📺 Pantalla TV"],
        key="modo_viz"
    )
    
    st.markdown("---")
    
    # Información del sistema
    st.markdown("### 🕐 Sistema")
    now_bog = datetime.now(ZoneInfo("America/Bogota"))
    now_server = now_bog + timedelta(hours=OFFSET_HOURS)
    
    st.info(f"**Bogotá:** {now_bog.strftime('%H:%M:%S')}")
    st.info(f"**Servidor:** {now_server.strftime('%H:%M:%S')}")
    st.caption(f"Desfase: +{OFFSET_HOURS}h")
    
    st.markdown("---")
    
    # Límites SLA
    with st.expander("📋 Límites SLA"):
        st.markdown("""
        - **Muy Alta:** 4 horas
        - **Alta:** 8 horas  
        - **Media:** 16 horas (2 días)
        - **Baja:** 32 horas (4 días)
        - **Muy Baja:** 2 minutos
        """)
    
    st.markdown("---")
    st.caption("GIA v2.0 | IPS Goleman")

# ==========================================
# CONTENIDO PRINCIPAL
# ==========================================

# Título principal
st.markdown("""
<div style='text-align:center; padding: 20px 0;'>
    <h1 style='font-size: 48px; margin: 0;'>🎯 GIA</h1>
    <p style='font-size: 18px; color: rgba(255,255,255,0.7); margin: 5px 0;'>
        Sistema Inteligente de Análisis SLA
    </p>
</div>
""", unsafe_allow_html=True)

# Subir archivo
uploaded = st.file_uploader(
    "📂 Cargar archivo CSV de GIA",
    type=["csv"],
    help="Sube el reporte exportado desde GLPI/GIA"
)

if not uploaded:
    st.info("👆 Sube un archivo CSV para comenzar el análisis")
    st.stop()

# Leer y procesar datos
try:
    df = pd.read_csv(uploaded, sep=";", encoding="utf-8")
except:
    df = pd.read_csv(uploaded, sep=",", encoding="utf-8")

# Verificar columnas
required_cols = ["ID", "Estados", "Fecha de apertura", "Prioridad", "Asignado a - Técnico"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"❌ Faltan columnas: {', '.join(missing)}")
    st.stop()

df_procesado = procesar_datos(df)
col_tec = "Asignado a - Técnico"

# ==========================================
# MODO DASHBOARD COMPLETO
# ==========================================
if modo == "📊 Dashboard Completo":
    
    # Filtros
    with st.expander("🔍 Filtros", expanded=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            tecnicos = ["Todos"] + sorted(df_procesado[col_tec].dropna().unique().tolist())
            tec_sel = st.selectbox("👤 Técnico", tecnicos)
        
        with col_f2:
            prioridades = ["Todas"] + sorted(df_procesado["Prioridad"].dropna().unique().tolist())
            prior_sel = st.selectbox("⚡ Prioridad", prioridades)
    
    # Aplicar filtros
    df_filtrado = df_procesado.copy()
    if tec_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_tec] == tec_sel]
    if prior_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Prioridad"] == prior_sel]
    
    resumen = generar_resumen(df_filtrado, col_tec)
    
    # KPIs principales
    st.markdown("### 📊 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_asignados = int(resumen["Asignados"].sum())
    total_resueltos = int(resumen["Resueltos"].sum())
    total_tardios = int(resumen["Tardíos"].sum())
    sla_promedio = resumen["SLA (%)"].mean() if not resumen.empty else 0.0
    
    with col1:
        st.markdown(crear_tarjeta_metrica("ASIGNADOS", total_asignados, "📋"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(crear_tarjeta_metrica("RESUELTOS", total_resueltos, "✅"), unsafe_allow_html=True)
    
    with col3:
        st.markdown(crear_tarjeta_metrica("TARDÍOS", total_tardios, "⏰"), unsafe_allow_html=True)
    
    with col4:
        st.markdown(crear_tarjeta_metrica("SLA GLOBAL", f"{sla_promedio:.1f}%", "🎯"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 📈 Cumplimiento SLA por Técnico")
        if not resumen.empty:
            fig = px.bar(
                resumen.sort_values("SLA (%)", ascending=False),
                x=col_tec, y="SLA (%)",
                color="SLA (%)",
                color_continuous_scale=["#EE5A6F", "#F79F1F", "#10AC84"],
                text_auto=".1f"
            )
            fig.update_layout(
                template="plotly_dark",
                height=400,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("#### 🥧 Distribución de Casos")
        cerrados = df_filtrado[df_filtrado["Resuelto"] == True]
        if not cerrados.empty:
            cumplidos = (cerrados["Estado SLA"] == "Cumplido").sum()
            tardios = (cerrados["Estado SLA"] == "Tardío").sum()
            
            fig_pie = px.pie(
                pd.DataFrame({"Estado": ["Cumplido", "Tardío"], "Cantidad": [cumplidos, tardios]}),
                names="Estado", values="Cantidad",
                color="Estado",
                color_discrete_map={"Cumplido": "#10AC84", "Tardío": "#EE5A6F"},
                hole=0.4
            )
            fig_pie.update_layout(
                template="plotly_dark",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay casos cerrados para mostrar.")
    
    # Tabla de técnicos
    st.markdown("### 👥 Ranking de Técnicos")
            cumplidos = (cerrados["Estado SLA"] == "Cumplido").sum()
            tardios = (cerrados["Estado SLA"] == "Tardío").sum()
            
            fig_pie = px.pie(
                pd.DataFrame({"Estado": ["Cumplido", "Tardío"], "Cantidad": [cumplidos, tardios]}),
                names="Estado", values="Cantidad",
                color="Estado",
                color_discrete_map={"Cumplido": "#10AC84", "Tardío": "#EE5A6F"},
                hole=0.4
            )
            fig_pie.update_layout(
                template="plotly_dark",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tabla de técnicos
    st.markdown("### 👥 Ranking de Técnicos")
    
    # Agregar medallas
    resumen_display = resumen.sort_values("SLA (%)", ascending=False).copy()
    resumen_display.insert(0, "Rank", ["🥇", "🥈", "🥉"] + [""] * (len(resumen_display) - 3))
    
    st.dataframe(
        resumen_display,
        use_container_width=True,
        hide_index=True,
        height=300
    )
    
    # Detalle de casos
    st.markdown("### 📝 Detalle de Casos")
    
    df_display = df_filtrado.copy()
    df_display["Fecha Cierre"] = df_display["Fecha Cierre"].apply(
        lambda x: "Sin cerrar" if pd.isna(x) else x
    )
    
    cols_mostrar = ["ID", "Título", "Estados", col_tec, "Prioridad", 
                    "Fecha Apertura", "Fecha Cierre",
                    "Minutos Hábiles", "SLA Límite (min)", "Estado SLA"]
    
    def highlight_tardios(row):
        if "Tardío" in str(row["Estado SLA"]):
            return ['background-color: #EE5A6F; color: white; font-weight: bold'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        df_display[cols_mostrar].style.apply(highlight_tardios, axis=1),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Descargar reporte
    st.markdown("### 📥 Exportar Datos")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        csv = df_display[cols_mostrar].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar CSV",
            data=csv,
            file_name=f"gia_sla_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# ==========================================
# MODO PANTALLA TV
# ==========================================
else:
    if 'tv_index' not in st.session_state:
        st.session_state.tv_index = 0
    
    resumen = generar_resumen(df_procesado, col_tec)
    tecnicos = resumen.sort_values("SLA (%)", ascending=False).reset_index(drop=True)
    total = len(tecnicos)
    
    idx = st.session_state.tv_index % (total + 1)
    
    placeholder = st.empty()
    
    with placeholder.container():
        if idx == total:
            # Vista global
            st.markdown("<h1 style='text-align:center;'>🌍 RESUMEN GLOBAL</h1>", unsafe_allow_html=True)
            
            sla_g = resumen["SLA (%)"].mean()
            color = "#10AC84" if sla_g >= 90 else "#F79F1F" if sla_g >= 70 else "#EE5A6F"
            
            st.markdown(f"""
            <div style='text-align:center; padding: 60px 0;'>
                <div style='color:{color}; font-size:160px; font-weight:900;'>
                    {sla_g:.1f}%
                </div>
                <div style='color:rgba(255,255,255,0.6); font-size:24px;'>
                    SLA Global del Equipo
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Ranking
            for i, row in tecnicos.iterrows():
                sla = row["SLA (%)"]
                c = "#10AC84" if sla >= 90 else "#F79F1F" if sla >= 70 else "#EE5A6F"
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.05); padding:24px; margin:12px 0; 
                            border-left:5px solid {c}; border-radius:12px;
                            display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:32px;'>{medal} {row[col_tec]}</span>
                    <span style='color:{c}; font-size:36px; font-weight:900;'>{sla:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Vista individual
            tec = tecnicos.iloc[idx]
            sla = tec["SLA (%)"]
            color = "#10AC84" if sla >= 90 else "#F79F1F" if sla >= 70 else "#EE5A6F"
            
            st.markdown(f"""
            <div style='text-align:center;'>
                <div style='color:rgba(255,255,255,0.5); font-size:20px; margin-bottom:10px;'>
                    POSICIÓN #{idx+1} DE {total}
                </div>
                <h1 style='font-size:56px; margin:20px 0;'>
                    {tec[col_tec]}
                </h1>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='text-align:center; padding:80px 40px; margin:40px 0;
                        background:rgba(255,255,255,0.05); border-radius:24px;
                        border:3px solid {color};'>
                <div style='color:rgba(255,255,255,0.6); font-size:24px; margin-bottom:20px;'>
                    CUMPLIMIENTO SLA
                </div>
                <div style='color:{color}; font-size:180px; font-weight:900; line-height:1;'>
                    {sla:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(crear_tarjeta_metrica("ASIGNADOS", int(tec['Asignados']), "📋"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(crear_tarjeta_metrica("RESUELTOS", int(tec['Resueltos']), "✅"), unsafe_allow_html=True)
            
            with col3:
                st.markdown(crear_tarjeta_metrica("TARDÍOS", int(tec['Tardíos']), "⏰"), unsafe_allow_html=True)
    
    time_module.sleep(5)
    st.session_state.tv_index += 1
    st.rerun()
