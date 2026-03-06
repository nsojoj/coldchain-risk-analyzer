import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from modelo import (
    calcular_tasa_sublimacion,
    calcular_duracion_hielo,
    analizar_escenarios,
    simulacion_monte_carlo,
    hielo_minimo_recomendado,
    generar_curva_sublimacion,
)

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ColdChain Risk Analyzer",
    page_icon="❄️",
    layout="wide",
)

st.markdown("""
<style>
    .metric-card {
        background: #0d1b2a;
        border: 1px solid #1e3a52;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .risk-high { color: #ff4d4d; font-size: 2rem; font-weight: 800; }
    .risk-mid  { color: #f0b429; font-size: 2rem; font-weight: 800; }
    .risk-low  { color: #00e5a0; font-size: 2rem; font-weight: 800; }
    .section-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 2px;
        color: #7a9bb5;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("## ❄️ ColdChain Risk Analyzer")
st.divider()

# ── Sidebar — Parámetros ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📦 Parámetros del envío")

    peso_prod = st.number_input("Peso del producto (kg)", min_value=1.0, max_value=5000.0, value=50.0, step=1.0)
    hielo_seco = st.number_input("Hielo seco (kg)", min_value=0.5, max_value=500.0, value=10.0, step=0.5)
    temp_amb = st.slider("Temperatura ambiente (°C)", min_value=-10, max_value=50, value=25)
    duracion = st.number_input("Duración estimada (h)", min_value=0.5, max_value=120.0, value=8.0, step=0.5)
    aislamiento = st.selectbox("Nivel de aislamiento", ["Alto", "Medio", "Bajo"])
    prob_retraso = st.slider("Probabilidad de retraso (%)", min_value=0, max_value=100, value=30) / 100

    st.divider()
    n_sim = st.select_slider("Simulaciones Monte Carlo", options=[1000, 2000, 5000, 10000], value=5000)

    calcular = st.button("🔄 Calcular", use_container_width=True, type="primary")

# ── Cálculos ──────────────────────────────────────────────────────────────────
tasa = calcular_tasa_sublimacion(temp_amb, aislamiento)
dur_hielo = calcular_duracion_hielo(hielo_seco, tasa)
escenarios = analizar_escenarios(dur_hielo, duracion, prob_retraso)
hielo_min = hielo_minimo_recomendado(tasa, escenarios["tiempo_retraso"])
mc = simulacion_monte_carlo(hielo_seco, temp_amb, aislamiento, duracion, prob_retraso, n_sim)

prob_fallo = mc["prob_fallo_mc"]
color_riesgo = "risk-high" if prob_fallo >= 50 else ("risk-mid" if prob_fallo >= 20 else "risk-low")
emoji_riesgo = "🔴" if prob_fallo >= 50 else ("🟡" if prob_fallo >= 20 else "🟢")

# ── Métricas principales ──────────────────────────────────────────────────────
st.markdown('<p class="section-title">MODELO DE SUBLIMACIÓN</p>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Tasa de sublimación", f"{tasa:.4f} kg/h")
with col2:
    st.metric("Duración hielo seco", f"{dur_hielo:.2f} h")
with col3:
    st.metric("Hielo mínimo recomendado", f"{hielo_min:.2f} kg",
              delta=f"{hielo_seco - hielo_min:.2f} kg vs actual",
              delta_color="normal")
with col4:
    st.metric(f"{emoji_riesgo} Probabilidad de fallo (MC)", f"{prob_fallo:.1f}%")

st.divider()

# ── Escenarios ────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">ANÁLISIS DE ESCENARIOS</p>', unsafe_allow_html=True)
col_n, col_r = st.columns(2)

with col_n:
    ok = not escenarios["fallo_normal"]
    margen = dur_hielo - escenarios["tiempo_normal"]
    st.markdown(f"**🚚 Escenario normal — {escenarios['tiempo_normal']:.1f} h**")
    st.metric("Margen de hielo", f"{margen:+.2f} h")
    if ok:
        st.success("✅ Cadena de frío mantenida")
    else:
        st.error("❌ Riesgo de ruptura de cadena de frío")

with col_r:
    ok_r = not escenarios["fallo_retraso"]
    margen_r = dur_hielo - escenarios["tiempo_retraso"]
    st.markdown(f"**⚠️ Escenario con retraso +40% — {escenarios['tiempo_retraso']:.1f} h**")
    st.metric("Margen de hielo", f"{margen_r:+.2f} h")
    if ok_r:
        st.success("✅ Cadena de frío mantenida")
    else:
        st.error("❌ Riesgo de ruptura de cadena de frío")

st.divider()

# ── Gráficas ──────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">VISUALIZACIONES</p>', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📉 Curva de sublimación", "📊 Simulación Monte Carlo"])

with tab1:
    tiempos_curva, hielo_restante = generar_curva_sublimacion(hielo_seco, tasa, duracion)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=tiempos_curva, y=hielo_restante,
        name="Hielo restante", line=dict(color="#00cfff", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,207,255,0.08)"
    ))
    fig1.add_vline(x=duracion, line_dash="dash", line_color="#f0b429",
                   annotation_text=f"Viaje normal ({duracion}h)", annotation_position="top right")
    fig1.add_vline(x=escenarios["tiempo_retraso"], line_dash="dash", line_color="#ff4d4d",
                   annotation_text=f"Con retraso ({escenarios['tiempo_retraso']:.1f}h)", annotation_position="top left")
    fig1.add_hline(y=0, line_color="rgba(255,255,255,0.27)")

    fig1.update_layout(
        template="plotly_dark", height=380,
        xaxis_title="Tiempo (h)", yaxis_title="Hielo seco restante (kg)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=40)
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    col_hist, col_scatter = st.columns(2)

    with col_hist:
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=mc["margenes"], nbinsx=60,
            marker_color=np.where(mc["margenes"] >= 0, "#00e5a0", "#ff4d4d")[0]
            if False else "#00e5a0",
            name="Margen (h)"
        ))
        # Colorear barras por color distinto para fallidos
        margenes_arr = mc["margenes"]
        fig2.add_trace(go.Histogram(
            x=margenes_arr[margenes_arr < 0], nbinsx=40,
            marker_color="#ff4d4d", name="Fallo"
        ))
        fig2.add_trace(go.Histogram(
            x=margenes_arr[margenes_arr >= 0], nbinsx=40,
            marker_color="#00e5a0", name="OK"
        ))
        fig2.add_vline(x=0, line_color="white", line_dash="dot")
        fig2.update_layout(
            template="plotly_dark", height=320, barmode="overlay",
            title="Distribución de márgenes de seguridad",
            xaxis_title="Margen (h)", yaxis_title="Frecuencia",
            showlegend=True, margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_scatter:
        sample = min(1000, n_sim)
        idx = np.random.choice(len(mc["tiempos_sim"]), sample, replace=False)
        fig3 = px.scatter(
            x=mc["tiempos_sim"][idx],
            y=mc["duraciones_hielo"][idx],
            color=mc["fallos"][idx].astype(int),
            color_discrete_map={0: "#00e5a0", 1: "#ff4d4d"},
            labels={"x": "Tiempo viaje (h)", "y": "Duración hielo (h)", "color": "Fallo"},
            title=f"Dispersión: {sample} simulaciones",
            template="plotly_dark", height=320
        )
        fig3.add_shape(type="line", x0=0, x1=1, y0=0, y1=1,
                       xref="paper", yref="paper",
                       line=dict(color="white", dash="dot", width=1))
        fig3.update_layout(margin=dict(t=40, b=40))
        st.plotly_chart(fig3, use_container_width=True)

    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Percentil 5 del margen", f"{mc['percentil_5_margen']:.2f} h")
    col_p2.metric("Margen promedio", f"{mc['media_margen']:.2f} h")
    col_p3.metric("Percentil 95 del margen", f"{mc['percentil_95_margen']:.2f} h")

st.divider()

# ── Recomendaciones automáticas ───────────────────────────────────────────────
st.markdown('<p class="section-title">RECOMENDACIONES LOGÍSTICAS</p>', unsafe_allow_html=True)

deficit = hielo_min - hielo_seco
margen_p5 = mc["percentil_5_margen"]

if prob_fallo >= 50:
    st.error(f"🔴 **Riesgo ALTO ({prob_fallo:.1f}%)** — La configuración actual presenta una probabilidad de fallo superior al 50%. Se recomienda no despachar sin ajustes.")
elif prob_fallo >= 20:
    st.warning(f"🟡 **Riesgo MODERADO ({prob_fallo:.1f}%)** — Existen escenarios plausibles de ruptura de cadena de frío. Revisar cantidad de hielo y aislamiento.")
else:
    st.success(f"🟢 **Riesgo BAJO ({prob_fallo:.1f}%)** — La configuración actual es adecuada para las condiciones del envío.")

col_r1, col_r2 = st.columns(2)

with col_r1:
    st.markdown("**📋 Diagnóstico del envío**")
    if deficit > 0:
        st.markdown(f"- ⚠️ Déficit de hielo seco: necesitas **{deficit:.2f} kg adicionales** para cubrir escenario con retraso + margen del 15%.")
    else:
        st.markdown(f"- ✅ Hielo seco suficiente: tienes **{abs(deficit):.2f} kg de excedente** sobre el mínimo recomendado.")

    if margen_p5 < 0:
        st.markdown(f"- ⚠️ En el peor 5% de escenarios Monte Carlo, el hielo se agota **{abs(margen_p5):.2f} h antes** de llegar al destino.")
    else:
        st.markdown(f"- ✅ En el peor 5% de escenarios, aún quedan **{margen_p5:.2f} h de margen** de hielo.")

    if aislamiento == "Bajo":
        st.markdown("- ⚠️ El aislamiento **Bajo** aumenta la tasa de sublimación en un 40% vs aislamiento Medio. Considera mejorar el empaque.")
    elif aislamiento == "Medio":
        st.markdown("- 💡 Mejorar a aislamiento **Alto** reduciría la tasa de sublimación un 40% y extendería la duración del hielo.")

with col_r2:
    st.markdown("**🛠️ Acciones recomendadas**")
    acciones = []

    if deficit > 0:
        acciones.append(f"Aumentar hielo seco a mínimo **{hielo_min:.1f} kg** para cubrir retrasos con margen de seguridad.")
    if aislamiento != "Alto":
        acciones.append("Actualizar a empaque de aislamiento **Alto** para reducir consumo de hielo en un 40%.")
    if prob_retraso > 0.4:
        acciones.append("Probabilidad de retraso alta (>40%): considerar **ruta alternativa** o proveedor de transporte con mejor cumplimiento.")
    if temp_amb > 35:
        acciones.append("Temperatura ambiente crítica (>35°C): programar despachos en **horario nocturno** para reducir exposición térmica.")
    acciones.append(f"Hielo mínimo operativo para esta ruta: **{hielo_min:.2f} kg** — estandarizar en el protocolo de despacho.")

    for a in acciones:
        st.markdown(f"- {a}")
