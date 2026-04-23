from pathlib import Path

import streamlit as st

from components.pwm_plot import append_sample, build_figure, init_history

st.set_page_config(page_title="Control System Incubator", layout="wide")


def load_styles() -> None:
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_styles()

st.markdown(
    "<h1 style='text-align: center;'>Control System Incubator Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center;'>Monitoramento de PWM e temperatura para incubadora</p>",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = init_history(history_size=50)

if "fan_failure" not in st.session_state:
    st.session_state.fan_failure = False

if "system_failure" not in st.session_state:
    st.session_state.system_failure = False

# Simulated data is updated once every app rerun.
st.session_state.history = append_sample(
    st.session_state.history,
    fan_failure=st.session_state.fan_failure,
    system_failure=st.session_state.system_failure,
)

latest_pwm = st.session_state.history["pwm"][-1]
latest_temp = st.session_state.history["temp"][-1]

_, col_metrics, _ = st.columns([1.4, 3.2, 1.4])
with col_metrics:
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("PWM atual", f"{latest_pwm:.1f}%")
    col_m2.metric("Temperatura atual", f"{latest_temp:.2f} °C")

if st.session_state.fan_failure:
    st.error("Falha da ventoinha ativa: tendência de aumento de temperatura.")

if st.session_state.system_failure:
    st.error("Falha do sistema ativa: PWM forçado para 0%.")

st.markdown(
    "<h3 style='text-align: center;'>PWM / Temperatura em tempo real</h3>",
    unsafe_allow_html=True,
)
st.plotly_chart(build_figure(st.session_state.history), use_container_width=True)

_, col_buttons, _ = st.columns([1, 2, 1])
with col_buttons:
    if st.button("Falha da Ventoinha", use_container_width=True):
        st.session_state.fan_failure = not st.session_state.fan_failure
    if st.button("Falha do Sistema", use_container_width=True):
        st.session_state.system_failure = not st.session_state.system_failure
