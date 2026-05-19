from pathlib import Path
import base64
from html import escape
import urllib.request
import urllib.error
import json

import streamlit as st

from backend.backend import (
    build_snapshot,
    init_dashboard_state,
    update_telemetry,
    reset_system,
    resolve_state_image,
    toggle_fan_failure,
    toggle_system_failure,
    update_pwm_user,
    add_event,
)
from components.pwm_plot import build_pwm_figure, build_temperature_figure
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Sistema de Controle da Incubadora", page_icon="🏭", layout="wide")

# ── Configuração Node-RED ─────────────────────────────────────────────────────
NODE_RED_URL = "http://localhost:1880/pwm"
TIMEOUT_S = 3.0
# ─────────────────────────────────────────────────────────────────────────────


def _decode_response_message(body: bytes) -> str | None:
    if not body:
        return None

    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text

    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("msg") or payload.get("status")
        if message:
            return str(message)

    return text


def send_pwm_to_nodered(pwm_value: float) -> dict:
    payload = json.dumps({"pwm": round(pwm_value, 2)}).encode("utf-8")
    req = urllib.request.Request(
        NODE_RED_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            response_body = resp.read()
            response_message = _decode_response_message(response_body)
            return {
                "ok": True,
                "message": response_message or f"PWM {pwm_value:.1f}% enviado com sucesso",
            }
    except urllib.error.HTTPError as exc:
        response_message = _decode_response_message(exc.read())
        return {
            "ok": False,
            "message": response_message or f"Erro HTTP {exc.code}: {exc.reason}",
        }
    except urllib.error.URLError as exc:
        return {"ok": False, "message": f"Node-RED inacessível: {exc.reason}"}
    except Exception as exc:
        return {"ok": False, "message": f"Erro inesperado: {exc}"}


def load_styles() -> None:
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_styles()


def render_incubator_asset(image_path: Path) -> None:
    if not image_path.exists():
        st.markdown("<div class='incubator-asset'></div>", unsafe_allow_html=True)
        return

    cached_path = st.session_state.get("_incubator_cached_path")
    cached_b64 = st.session_state.get("_incubator_cached_b64")

    current_path_str = str(image_path.resolve())
    if cached_path == current_path_str and cached_b64:
        encoded_image = cached_b64
    else:
        encoded_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        st.session_state["_incubator_cached_path"] = current_path_str
        st.session_state["_incubator_cached_b64"] = encoded_image

    st.markdown(
        f"""
        <div class='incubator-asset'>
          <img class='incubator-img' src='data:image/png;base64,{encoded_image}' alt='Estado incubadora' />
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pwm_slider() -> None:
    """Render PWM control with number input. Envia somente ao confirmar com Enter."""

    if "pwm_slider_value" not in st.session_state:
        st.session_state.pwm_slider_value = 0.0

    current_value = st.session_state.pwm_slider_value

    st.markdown(
        f"""
        <div class='control-summary'>
            <div class='pwm-display-left'>
                <div class='pwm-value-label'>Percentual selecionado</div>
                <div class='pwm-value-large'>{current_value}%</div>
            </div>
            <div class='pwm-display-right'>
                <div class='pwm-output-label'>Segundos de Referencia</div>
                <div class='pwm-value-seconds'>100% = 40s </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='pwm-title' style='margin-top: 0.6rem; margin-bottom: 0.4rem;'>Selecione o PWM</div>",
        unsafe_allow_html=True,
    )

    with st.form("pwm_input_form", clear_on_submit=False):
        input_col, button_col = st.columns([3, 1], gap="small")

        with input_col:
            st.number_input(
                "PWM Value",
                min_value=0,
                max_value=100,
                value=int(current_value),
                label_visibility="collapsed",
                key="pwm_input_number",
                step=1,
            )

        with button_col:
            submitted = st.form_submit_button("Enviar")

    if submitted:
        pwm_to_send = float(st.session_state.pwm_input_number)
        result = send_pwm_to_nodered(pwm_to_send)
        if result["ok"]:
            update_pwm_user(st.session_state, pwm_to_send)
            st.toast(f"✅ {result['message']}", icon="📡")
            add_event(st.session_state, f"PWM {pwm_to_send:.1f}% enviado ao Node-RED", level="ok")
        else:
            st.toast(f"❌ {result['message']}", icon="⚠️")

def sparkline_svg(values: list[float], color: str, stepped: bool = False) -> str:
    if not values:
        return ""

    width = 220
    height = 62
    min_v = min(values)
    max_v = max(values)
    span = max(max_v - min_v, 1e-6)

    points = []
    step_x = width / max(len(values) - 1, 1)
    last_y = None
    for idx, val in enumerate(values):
        x = idx * step_x
        y = height - ((val - min_v) / span) * (height - 8) - 4
        if stepped and last_y is not None:
            points.append(f"{x:.2f},{last_y:.2f}")
        points.append(f"{x:.2f},{y:.2f}")
        last_y = y

    polyline = " ".join(points)
    return (
        "<svg viewBox='0 0 220 62' class='sparkline'>"
        f"<polyline fill='none' stroke='{escape(color)}' stroke-width='3.2' "
        "stroke-linecap='round' stroke-linejoin='round' "
        f"points='{polyline}'></polyline></svg>"
    )


def render_kpi_card(
    title: str,
    value: str,
    icon: str,
    trend_values: list[float],
    trend_text: str,
    tone: str,
    stepped: bool = False,
) -> None:
    trend_color = {
        "warm": "#F28C28",
        "ok": "#2D9C49",
        "alert": "#D62828",
    }.get(tone, "#F28C28")

    sparkline = sparkline_svg(trend_values[-14:], trend_color, stepped=stepped)
    st.markdown(
        f"""
        <div class='kpi-card tone-{escape(tone)}'>
          <div class='kpi-top'>
            <span class='kpi-icon'>{escape(icon)}</span>
            <span class='kpi-title'>{escape(title)}</span>
          </div>
          <div class='kpi-value'>{escape(value)}</div>
          <div class='kpi-trend'>{escape(trend_text)}</div>
          {sparkline}
        </div>
        """,
        unsafe_allow_html=True,
    )


init_dashboard_state(st.session_state)

def render_dashboard_cycle() -> None:
    if st.session_state.automatic_process:
        update_telemetry(st.session_state, interval_s=1.0)

    snapshot = build_snapshot(st.session_state)

    latest_pwm = snapshot["latest_pwm"]
    latest_temp = snapshot["latest_temp"]
    setpoint = snapshot["setpoint"]
    lamp_on = snapshot["lamp_on"]
    state_label = snapshot["state_label"]
    state_tone = snapshot["state_tone"]
    status_text = snapshot["status_text"]
    backend_state = snapshot["backend_state"]

    header_col_left, header_col_right = st.columns([3.2, 1.0], gap="small")

    with header_col_left:
        st.markdown(
            """
            <div class='hero-card'>
              <div class='hero-title'>Controle da Incubadora | Monitor Industrial</div>
              <div class='hero-subtitle'>Monitoramento em tempo real de temperatura e atuação PWM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_col_right:
        image_path = resolve_state_image(backend_state)
        render_incubator_asset(image_path)

    st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)

    top_left, top_right = st.columns([2.7, 1.0], gap="small")

    with top_left:
        st.markdown(
            """
            <div class='panel-title'>
                Tendência Dinâmica: PWM
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            build_pwm_figure(st.session_state.history),
            width="stretch",
            config={"displayModeBar": False},
        )

        st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class='panel-title'>
                Temperatura ao Longo do Tempo
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            build_temperature_figure(st.session_state.history),
            width="stretch",
            config={"displayModeBar": False},
        )

    with top_right:
        # Resumo com Temperatura e Status da Lâmpada
        lamp_status = "Ligada" if lamp_on else "Desligada"
        lamp_icon = "💡" if lamp_on else "🔌"
        
        st.markdown(
            f"""
            <div class='summary-card'>
              <div class='summary-row'>
                <div class='summary-item'>
                  <div class='summary-label'>Temperatura Atual</div>
                  <div class='summary-value'>🌡 {latest_temp:.2f} °C</div>
                </div>
                <div class='summary-item'>
                  <div class='summary-label'>Status da Lâmpada</div>
                  <div class='summary-value'>{lamp_icon} {lamp_status}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("<div class='section-gap-sm'></div>", unsafe_allow_html=True)
        st.markdown("<div class='control-card'><div class='control-title'>Painel de Controle</div>", unsafe_allow_html=True)

        st.markdown("<div class='control-body'>", unsafe_allow_html=True)
        render_pwm_slider()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div><div class='events-card'><div class='events-title'>Alarmes e Eventos</div>", unsafe_allow_html=True)
        if st.session_state.events:
            for event in st.session_state.events:
                lvl = event["level"]
                badge_class = "badge-info"
                if lvl == "ok":
                    badge_class = "badge-ok"
                elif lvl == "warn":
                    badge_class = "badge-warn"
                elif lvl == "alert":
                    badge_class = "badge-alert"

                st.markdown(
                    f"""
                    <div class='event-item'>
                      <span class='event-time'>{escape(event['time'])}</span>
                      <span class='event-text'>{escape(event['message'])}</span>
                      <span class='event-badge {badge_class}'>{escape(lvl.upper())}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.fan_failure:
        if st.session_state._prev_fan_failure != st.session_state.fan_failure:
            st.toast("Falha da ventoinha ativa", icon="⚠")
        st.session_state._prev_fan_failure = st.session_state.fan_failure

    if st.session_state.system_failure:
        if st.session_state._prev_system_failure != st.session_state.system_failure:
            st.toast("Falha crítica do sistema", icon="🚨")
        st.session_state._prev_system_failure = st.session_state.system_failure

    temp_alert_now = "low" if latest_temp < 20 else ("high" if latest_temp > 40 else "none")
    if temp_alert_now != st.session_state._prev_thermal_alert:
        if temp_alert_now != "none":
            st.toast("Temperatura fora da faixa crítica (20°C - 40°C)", icon="🌡")
        st.session_state._prev_thermal_alert = temp_alert_now


if hasattr(st, "fragment"):
    st.fragment(run_every="1s")(render_dashboard_cycle)()
else:
    render_dashboard_cycle()

logger.info("Dashboard initialized")