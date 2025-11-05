import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import unicodedata
import time as time_module

# Configuración
st.set_page_config(page_title="GIA - Sistema SLA", page_icon="🎯", layout="wide")

# Constantes
OFFSET_HOURS = 5.0
WORK_SCHEDULE = {
    0: [(time(7,0), time(17,0))], 1: [(time(7,0), time(17,0))],
    2: [(time(7,0), time(17,0))], 3: [(time(7,0), time(17,0))],
    4: [(time(7,0), time(16,0))], 5: [(time(8,0), time(13,0))], 6: []
}
SLA_HOURS = {"muy alta": 4, "alta": 8, "media": 16, "baja": 32, "muy baja": 2/60}

# CSS
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);}
.metric-card {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}
.metric-value {font-size: 42px; font-weight: 900; color: #667eea;}
.metric-label {font-size: 14px; color: rgba(255,255,255,0.7); text-transform: uppercase;}
h1, h2, h3 {color: white !important;}
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Funciones
def norm(s):
    if pd.isna(s): return ""
    s = str(s)
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn").lower().strip()

def to_timestamp(fecha_str):
    if pd.isna(fecha_str): return pd.NaT
    try:
        dt = pd.to_datetime(fecha_str, errors='coerce', dayfirst=True)
        return dt - timedelta(hours=OFFSET_HOURS) if pd.notna(dt) else pd.NaT
    except:
        return pd.NaT

def business_hours_between(start, end):
    if pd.isna(start) or pd.isna(end) or end <= start: return 0.0
    total_seconds = 0.0
    current = start
    for _ in range(400):
        current_date = current.date()
        weekday = current.weekday()
        if weekday not in WORK_SCHEDULE or not WORK_SCHEDULE[weekday]:
            next_day = datetime.combine(current_date + timedelta(days=1), time(0, 0))
            if next_day >= end: break
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
        if next_day >= end: break
        current = next_day
    return total_seconds / 3600.0

def get_sla_hours(priority):
    if pd.isna(priority): return 8.0
    p = norm(priority)
    if "muy baja" in p or "muybaja" in p: return 2/60
    elif "muy alta" in p or "muyalta" in p: return 4
    elif "alta" in p: return 8
    elif "media" in p: return 16
    elif "baja" in p: return 32
    return 8.0

def is_resolved(estado):
    e = norm(estado)
    return "resuel" in e or "cerr" in e or "solucion" in e

def procesar_datos(df):
    df["Fecha Apertura"] = df["Fecha de apertura"].apply(to_timestamp)
    df["Resuelto"] = df["Estados"].apply(is_resolved)
    df["Fecha Cierre"] = df.apply(lambda r: to_timestamp(r["Última modificación"]) if r["Resuelto"] else pd.NaT, axis=1)
    
    def calc_horas(row):
        if pd.isna(row["Fecha Apertura"]): return 0.0
        end_date = row["Fecha Cierre"] if row["Resuelto"] and pd.notna(row["Fecha Cierre"]) else datetime.now()
        return business_hours_between(row["Fecha Apertura"], end_date)
    
    df["Horas Hábiles"] = df.apply(calc_horas, axis=1)
    df["Minutos Hábiles"] = df["Horas Hábiles"] * 60
    df["SLA Límite (h)"] = df["Prioridad"].apply(get_sla_hours)
    df["SLA Límite (min)"] = df["SLA Límite (h)"] * 60
    
    def estado_sla(row):
        if not row["Resuelto"]:
            return "Abierto (Tardío)" if row["Horas Hábiles"] > row["SLA Límite (h)"] else "Abierto"
        return "Cumplido" if row["Horas Hábiles"] <= row["SLA Límite (h)"] else "Tardío"
    
    df["Estado SLA"] = df.apply(estado_sla, axis=1)
    df["Es Tardío"] = df["Estado SLA"].str.contains("Tardío")
    return df

def generar_resumen(df, col_tecnico):
    resumen = df.groupby(col_tecnico).agg(
        Asignados=("ID", "count"),
        Resueltos=("Resuelto", "sum"),
        Tardíos=("Es Tardío", "sum")
    ).reset_index()
    
    def calc_sla(row):
        if row["Resueltos"] == 0: return 0.0
        return ((row["Resueltos"] - row["Tardíos"]) / row["Resueltos"]) * 100
    
    resumen["SLA (%)"] = resumen.apply(calc_sla, axis=1)
    return resumen

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    modo = st.radio("Modo", ["📊 Dashboard", "📺 Pantalla TV"], key="modo")
    st.markdown("---")
    st.markdown("### 🕐 Sistema")
    now_bog = datetime.now(ZoneInfo("America/Bogota"))
    now_server = now_bog + timedelta(hours=OFFSET_HOURS)
    st.info(f"**Bogotá:** {now_bog.strftime('%H:%M:%S')}")
    st.info(f"**Servidor:** {now_server.strftime('%H:%M:%S')}")
    st.caption(f"Desfase: +{OFFSET_HOURS}h")
    st.markdown("---")
    with st.expander("📋 Límites SLA"):
        st.markdown("- **Muy Alta:** 4h\n- **Alta:** 8h\n- **Media:** 16h\n- **Baja:** 32h\n- **Muy Baja:** 2min")

# Título
st.markdown("<div style='text-align:center; padding:20px;'><h1 style='font-size:48px;'>🎯 GIA</h1><p style='color:rgba(255,255,255,0.7);'>Sistema de Análisis SLA</p></div>", unsafe_allow_html=True)

# Upload
uploaded = st.file_uploader("📂 Cargar CSV", type=["csv"])

if not uploaded:
    st.info("👆 Sube un archivo CSV")
    st.stop()

# Leer datos
try:
    df = pd.read_csv(uploaded, sep=";", encoding="utf-8")
except:
    df = pd.read_csv(uploaded, sep=",", encoding="utf-8")

required = ["ID", "Estados", "Fecha de apertura", "Prioridad", "Asignado a - Técnico"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"❌ Faltan columnas: {', '.join(missing)}")
    st.stop()

df_procesado = procesar_datos(df)
col_tec = "Asignado a - Técnico"

# MODO DASHBOARD
if modo == "📊 Dashboard":
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tecnicos = ["Todos"] + sorted(df_procesado[col_tec].dropna().unique().tolist())
            tec_sel = st.selectbox("👤 Técnico", tecnicos)
        with col2:
            prioridades = ["Todas"] + sorted(df_procesado["Prioridad"].dropna().unique().tolist())
            prior_sel = st.selectbox("⚡ Prioridad", prioridades)
    
    df_filtrado = df_procesado.copy()
    if tec_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_tec] == tec_sel]
    if prior_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Prioridad"] == prior_sel]
    
    resumen = generar_resumen(df_filtrado, col_tec)
    
    st.markdown("### 📊 Métricas")
    c1, c2, c3, c4 = st.columns(4)
    
    total_asig = int(resumen["Asignados"].sum())
    total_res = int(resumen["Resueltos"].sum())
    total_tard = int(resumen["Tardíos"].sum())
    sla_prom = resumen["SLA (%)"].mean() if not resumen.empty else 0.0
    
    with c1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>📋 ASIGNADOS</div><div class='metric-value'>{total_asig}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>✅ RESUELTOS</div><div class='metric-value'>{total_res}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>⏰ TARDÍOS</div><div class='metric-value'>{total_tard}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>🎯 SLA</div><div class='metric-value'>{sla_prom:.1f}%</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 📈 SLA por Técnico")
        if not resumen.empty:
            fig = px.bar(resumen.sort_values("SLA (%)", ascending=False), x=col_tec, y="SLA (%)",
                        color="SLA (%)", color_continuous_scale=["#EE5A6F", "#F79F1F", "#10AC84"], text_auto=".1f")
            fig.update_layout(template="plotly_dark", height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("#### 🥧 Distribución")
        cerrados = df_filtrado[df_filtrado["Resuelto"] == True]
        if not cerrados.empty:
            cumplidos = (cerrados["Estado SLA"] == "Cumplido").sum()
            tardios = (cerrados["Estado SLA"] == "Tardío").sum()
            fig_pie = px.pie(pd.DataFrame({"Estado": ["Cumplido", "Tardío"], "Cantidad": [cumplidos, tardios]}),
                           names="Estado", values="Cantidad", color="Estado",
                           color_discrete_map={"Cumplido": "#10AC84", "Tardío": "#EE5A6F"}, hole=0.4)
            fig_pie.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("### 👥 Ranking")
    resumen_display = resumen.sort_values("SLA (%)", ascending=False).copy()
    resumen_display.insert(0, "Rank", ["🥇", "🥈", "🥉"] + [""] * (len(resumen_display) - 3))
    st.dataframe(resumen_display, use_container_width=True, hide_index=True, height=300)
    
    st.markdown("### 📝 Detalle")
    df_display = df_filtrado.copy()
    df_display["Fecha Cierre"] = df_display["Fecha Cierre"].apply(lambda x: "Sin cerrar" if pd.isna(x) else x)
    cols = ["ID", "Título", "Estados", col_tec, "Prioridad", "Fecha Apertura", "Fecha Cierre", "Minutos Hábiles", "SLA Límite (min)", "Estado SLA"]
    
    def highlight(row):
        return ['background-color: #EE5A6F; color: white; font-weight: bold'] * len(row) if "Tardío" in str(row["Estado SLA"]) else [''] * len(row)
    
    st.dataframe(df_display[cols].style.apply(highlight, axis=1), use_container_width=True, hide_index=True, height=400)
    
    st.markdown("### 📥 Exportar")
    csv = df_display[cols].to_csv(index=False).encode('utf-8')
    st.download_button("📄 Descargar CSV", csv, f"gia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

# MODO TV
else:
    if 'tv_idx' not in st.session_state:
        st.session_state.tv_idx = 0
    
    resumen = generar_resumen(df_procesado, col_tec)
    tecnicos = resumen.sort_values("SLA (%)", ascending=False).reset_index(drop=True)
    total = len(tecnicos)
    idx = st.session_state.tv_idx % (total + 1)
    
    placeholder = st.empty()
    
    with placeholder.container():
        if idx == total:
            st.markdown("<h1 style='text-align:center;'>🌍 RESUMEN GLOBAL</h1>", unsafe_allow_html=True)
            sla_g = resumen["SLA (%)"].mean()
            color = "#10AC84" if sla_g >= 90 else "#F79F1F" if sla_g >= 70 else "#EE5A6F"
            st.markdown(f"<div style='text-align:center; padding:60px;'><div style='color:{color}; font-size:160px; font-weight:900;'>{sla_g:.1f}%</div></div>", unsafe_allow_html=True)
            for i, row in tecnicos.iterrows():
                sla = row["SLA (%)"]
                c = "#10AC84" if sla >= 90 else "#F79F1F" if sla >= 70 else "#EE5A6F"
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:24px; margin:12px; border-left:5px solid {c}; border-radius:12px;'><span style='font-size:32px;'>{medal} {row[col_tec]}</span><span style='float:right; color:{c}; font-size:36px; font-weight:900;'>{sla:.1f}%</span></div>", unsafe_allow_html=True)
        else:
            tec = tecnicos.iloc[idx]
            sla = tec["SLA (%)"]
            color = "#10AC84" if sla >= 90 else "#F79F1F" if sla >= 70 else "#EE5A6F"
            st.markdown(f"<div style='text-align:center;'><div style='color:rgba(255,255,255,0.5); font-size:20px;'>POSICIÓN #{idx+1} DE {total}</div><h1 style='font-size:56px; margin:20px;'>{tec[col_tec]}</h1></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; padding:80px 40px; margin:40px; background:rgba(255,255,255,0.05); border-radius:24px; border:3px solid {color};'><div style='color:rgba(255,255,255,0.6); font-size:24px;'>CUMPLIMIENTO SLA</div><div style='color:{color}; font-size:180px; font-weight:900;'>{sla:.1f}%</div></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>📋 ASIGNADOS</div><div class='metric-value'>{int(tec['Asignados'])}</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>✅ RESUELTOS</div><div class='metric-value'>{int(tec['Resueltos'])}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-card'><div class='metric-label'>⏰ TARDÍOS</div><div class='metric-value'>{int(tec['Tardíos'])}</div></div>", unsafe_allow_html=True)
    
    time_module.sleep(5)
    st.session_state.tv_idx += 1
    st.rerun()
