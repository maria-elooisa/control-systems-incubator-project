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
from components.pwm_plot import build_figure
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Sistema de Controle da Incubadora", page_icon="🏭", layout="wide")

# ── Configuração Node-RED ─────────────────────────────────────────────────────
NODE_RED_URL = "http://localhost:1880/pwm"
TIMEOUT_S = 3.0
# ─────────────────────────────────────────────────────────────────────────────


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
            return {"ok": True, "message": f"PWM {pwm_value:.1f}% enviado com sucesso"}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "message": f"Erro HTTP {exc.code}: {exc.reason}"}
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
    """Render PWM control card with slider. O valor só é enviado ao backend/Node-RED ao clicar no botão."""

    # Valor pendente: o que o usuário arrastou mas ainda não confirmou
    if "pwm_pending" not in st.session_state:
        st.session_state.pwm_pending = st.session_state.pwm_slider_value

    pending = st.session_state.pwm_pending
    is_max = pending >= 100
    seconds_value = round((pending / 100) * 60, 1)
    max_indicator = "⚡" if is_max else ""

    st.markdown(
        f"""
        <div class='control-summary'>
            <div class='pwm-display-left'>
                <div class='pwm-value-label'>Percentual selecionado</div>
                <div class='pwm-value-large'>{pending}%</div>
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
        "<div class='pwm-slider-wrap'><div class='pwm-title'>Selecione o PWM</div><div class='pwm-slider-center'>",
        unsafe_allow_html=True,
    )

    # O slider só atualiza pwm_pending — não toca no backend
    new_value = st.slider(
        "Selecione o PWM",
        min_value=0,
        max_value=100,
        value=pending,
        label_visibility="collapsed",
        key="pwm_slider_streamlit",
    )

    if new_value != pending:
        st.session_state.pwm_pending = new_value
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Botão: só aqui o valor é confirmado e enviado
    if st.button("Enviar valor", key="btn_send_pwm", width="stretch"):
        pwm_to_send = st.session_state.pwm_pending
        update_pwm_user(st.session_state, pwm_to_send)   # atualiza backend
        result = send_pwm_to_nodered(pwm_to_send)         # envia ao Node-RED
        if result["ok"]:
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

    header_col_left, header_col_mid, header_col_right = st.columns([2.2, 1.2, 1.0], gap="small")

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

    with header_col_mid:
        status_class = {
            "ok": "status-ok",
            "warn": "status-warn",
            "alert": "status-alert",
        }.get(state_tone, "status-ok")

        st.markdown(
            f"""
            <div class='status-card'>
              <div class='status-label'>Status Operacional</div>
              <div class='status-pill {status_class}'>{escape(status_text)}</div>
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
        kpi_c1, kpi_c2, kpi_c3 = st.columns([0.9, 0.9, 0.9], gap="small")

        with kpi_c1:
            render_kpi_card(
                title="Temperatura",
                value=f"{latest_temp:.2f} °C",
                icon="🌡",
                trend_values=st.session_state.history["temp"],
                trend_text="Leitura contínua",
                tone="warm",
            )

        with kpi_c2:
            lamp_status = "Ligada" if lamp_on else "Desligada"
            lamp_tone = "ok" if lamp_on else "warn"
            render_kpi_card(
                title="Lâmpada",
                value=lamp_status,
                icon="💡",
                trend_values=st.session_state.history["temp"],
                trend_text="Estado operacional",
                tone=lamp_tone,
            )

        with kpi_c3:
            render_kpi_card(
                title="Estado do Sistema",
                value=state_label,
                icon="🛡",
                trend_values=st.session_state.history["temp"],
                trend_text="Normal" if state_tone == "ok" else "Atenção",
                tone="ok" if state_tone == "ok" else "alert",
            )

        st.markdown("<div class='section-gap-md'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class='panel-title'>
              Tendência Dinâmica: PWM x Temperatura
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            build_figure(st.session_state.history),
            width="stretch",
            config={"displayModeBar": False},
        )

    with top_right:
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