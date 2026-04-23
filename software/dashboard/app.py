from pathlib import Path

import streamlit as st

from components.pwm_plot import append_sample, build_figure, init_history

st.set_page_config(page_title="Control System Incubator", layout="wide")


def load_styles() -> None:
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_styles()

# Fixed mock state for now; replace with backend value later.
backend_state = "ideal"  # accepted: "frio", "calor", "ideal"


def resolve_state_image(state: str) -> Path:
    state_map = {
        "frio": "ft-frio.png",
        "calor": "ft-calor.png",
        "ideal": "ft-ideal.png",
    }
    normalized_state = state.lower().strip()
    selected = state_map.get(normalized_state, state_map["ideal"])
    return Path(__file__).parent / "components" / "img" / selected

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

if "automatic_process" not in st.session_state:
    st.session_state.automatic_process = False

# Simulated data is updated once every app rerun.
st.session_state.history = append_sample(
    st.session_state.history,
    fan_failure=st.session_state.fan_failure,
    system_failure=st.session_state.system_failure,
)

latest_pwm = st.session_state.history["pwm"][-1]
latest_temp = st.session_state.history["temp"][-1]

col_left_top, col_metrics, col_image_top = st.columns([0.5, 2.7, 1.2])
with col_metrics:
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("PWM atual", f"{latest_pwm:.1f}%")
    col_m2.metric("Temperatura atual", f"{latest_temp:.2f} °C")

with col_image_top:
    st.markdown("<div class='status-image-top'>", unsafe_allow_html=True)
    image_path = resolve_state_image(backend_state)
    if image_path.exists():
        st.image(str(image_path), width=100)
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.fan_failure:
    st.error("Falha da ventoinha ativa: tendência de aumento de temperatura.")

if st.session_state.system_failure:
    st.error("Falha do sistema ativa: PWM forçado para 0%.")

if st.session_state.automatic_process:
    st.success("Processo automatico ativo: operacao em estado ideal.")

st.markdown(
    "<h3 style='text-align: center;'>PWM / Temperatura em tempo real</h3>",
    unsafe_allow_html=True,
)
st.plotly_chart(build_figure(st.session_state.history), use_container_width=True)

_, col_actions, _ = st.columns([0.8, 2.4, 0.8])
with col_actions:
    col_auto, col_sim = st.columns([1, 1.4])

    with col_auto:
        if st.button("Processo Automatico", type="primary", key="btn_auto", use_container_width=False):
            st.session_state.automatic_process = True
            st.session_state.fan_failure = False
            st.session_state.system_failure = False

    with col_sim:
        sim_box = st.container(border=True)
        with sim_box:
            st.markdown("<h4 style='text-align: center;'>Simulacao</h4>", unsafe_allow_html=True)
            if st.button("Falha da Ventoinha", key="btn_fan_failure", use_container_width=True):
                st.session_state.automatic_process = False
                st.session_state.fan_failure = not st.session_state.fan_failure

            if st.button("Falha do Sistema", key="btn_system_failure", use_container_width=True):
                st.session_state.automatic_process = False
                st.session_state.system_failure = not st.session_state.system_failure

        if st.session_state.fan_failure or st.session_state.system_failure:
            if st.button("Parar", key="btn_stop", use_container_width=True):
                st.session_state.automatic_process = False
                st.session_state.fan_failure = False
                st.session_state.system_failure = False
