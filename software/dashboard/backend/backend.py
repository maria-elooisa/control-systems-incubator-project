from __future__ import annotations

from time import monotonic
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .data_source import get_telemetry

from components.pwm_plot import init_history
import logging

logger = logging.getLogger(__name__)

SETPOINT_C = 37.0
TEMP_MIN_CRITICAL_C = 30.0
TEMP_MAX_CRITICAL_C = 40.0
IMAGE_MIN_C = 30.0
IMAGE_MAX_C = 37.0
DEFAULT_SAMPLE_INTERVAL_S = 1.0
MAX_CATCH_UP_SAMPLES = 5


def resolve_state_image(state: str) -> Path:
    state_map = {
        "frio": "ft-frio.png",
        "calor": "ft-calor.png",
        "ideal": "ft-ideal.png",
    }
    normalized_state = state.lower().strip()
    selected = state_map.get(normalized_state, state_map["ideal"])
    return Path(__file__).resolve().parent.parent / "components" / "img" / selected


def _ensure_history_time_series(session_state: Any) -> None:
    if "history" not in session_state or "time" in session_state.history:
        return

    history_size = len(session_state.history.get("x", []))
    now = datetime.now()
    session_state.history["time"] = [now - timedelta(seconds=(history_size - idx - 1)) for idx in range(history_size)]


def init_dashboard_state(session_state: Any) -> None:
    if "history" not in session_state:
        session_state.history = init_history(history_size=50)
    else:
        _ensure_history_time_series(session_state)

    if "fan_failure" not in session_state:
        session_state.fan_failure = False

    if "system_failure" not in session_state:
        session_state.system_failure = False

    if "automatic_process" not in session_state:
        session_state.automatic_process = True

    if "last_sample_monotonic" not in session_state:
        session_state.last_sample_monotonic = monotonic()

    if "events" not in session_state:
        session_state.events = []
        add_event(session_state, "Dashboard iniciado", level="ok")

    if "thermal_alert" not in session_state:
        session_state.thermal_alert = "none"
    
    # Lamp state initialization
    if "lamp_on" not in session_state:
        session_state.lamp_on = False
    
    # PWM user control initialization
    if "pwm_slider_value" not in session_state:
        session_state.pwm_slider_value = 0
    
    if "pwm_user" not in session_state:
        session_state.pwm_user = 0
    
    # previous-state trackers to avoid repeated UI notifications
    if "_prev_fan_failure" not in session_state:
        session_state._prev_fan_failure = session_state.fan_failure
    if "_prev_system_failure" not in session_state:
        session_state._prev_system_failure = session_state.system_failure
    if "_prev_thermal_alert" not in session_state:
        session_state._prev_thermal_alert = session_state.thermal_alert


def add_event(session_state: Any, message: str, level: str = "info") -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    session_state.events.insert(0, {"time": timestamp, "message": message, "level": level})
    session_state.events = session_state.events[:6]


def tick(session_state: Any) -> None:
    data = get_telemetry()

    temp = data["temp"]
    # PWM no dashboard é dirigido exclusivamente pelo usuário (slider 0-100).
    pwm = float(session_state.get("pwm_slider_value", 0))

    # log dos valores recebidos para inspeção no terminal
    logger.info(f"tick -> temp={temp!r}, pwm_user_slider={pwm!r}")

    session_state.history["x"].append(session_state.history["x"][-1] + 1)
    session_state.history.setdefault("time", []).append(datetime.now())
    session_state.history["temp"].append(temp)
    session_state.history["pwm"].append(pwm)

    for key in ("x", "time", "pwm", "temp"):
        session_state.history[key] = session_state.history[key][-50:]

    latest_temp = session_state.history["temp"][-1]
    thermal_alert = "none"
    if latest_temp < TEMP_MIN_CRITICAL_C:
        thermal_alert = "low"
    elif latest_temp > TEMP_MAX_CRITICAL_C:
        thermal_alert = "high"

    if thermal_alert != session_state.thermal_alert:
        if thermal_alert == "low":
            add_event(session_state, "Temperatura crítica baixa (< 20°C)", level="alert")
        elif thermal_alert == "high":
            add_event(session_state, "Temperatura crítica alta (> 40°C)", level="alert")
        elif session_state.thermal_alert != "none":
            add_event(session_state, "Temperatura retornou para faixa segura", level="ok")

    session_state.thermal_alert = thermal_alert


def update_telemetry(session_state: Any, interval_s: float = DEFAULT_SAMPLE_INTERVAL_S) -> int:
    """Generate new samples according to elapsed time and return generated count."""
    now = monotonic()
    elapsed = now - session_state.last_sample_monotonic
    if elapsed < interval_s:
        return 0

    sample_count = min(int(elapsed // interval_s), MAX_CATCH_UP_SAMPLES)
    for _ in range(sample_count):
        tick(session_state)

    session_state.last_sample_monotonic += sample_count * interval_s

    logger.info(f"update_telemetry -> elapsed={elapsed:.3f}s, sample_count={sample_count}")

    return sample_count


def compute_system_state(session_state: Any) -> tuple[str, str]:
    latest_temp = session_state.history["temp"][-1]
    if latest_temp < TEMP_MIN_CRITICAL_C or latest_temp > TEMP_MAX_CRITICAL_C:
        return "Crítico", "alert"
    if session_state.system_failure:
        return "Alerta", "alert"
    if session_state.fan_failure:
        return "Alerta", "warn"
    return "Normal", "ok"


def compute_backend_state(session_state: Any) -> str:
    """Resolve image state from temperature band only."""
    latest_temp = session_state.history["temp"][-1]

    if latest_temp < IMAGE_MIN_C:
        return "frio"
    if latest_temp > IMAGE_MAX_C:
        return "calor"

    return "ideal"


def status_text(session_state: Any) -> str:
    latest_temp = session_state.history["temp"][-1]
    if latest_temp < TEMP_MIN_CRITICAL_C:
        return "Temperatura Crítica Baixa"
    if latest_temp > TEMP_MAX_CRITICAL_C:
        return "Temperatura Crítica Alta"
    if session_state.system_failure:
        return "Falha Crítica"
    if session_state.fan_failure:
        return "Falha Ventoinha"
    return "Sistema Estável"


def toggle_fan_failure(session_state: Any) -> None:
    session_state.fan_failure = not session_state.fan_failure
    if session_state.fan_failure:
        add_event(session_state, "Falha da ventoinha acionada", level="warn")
    else:
        add_event(session_state, "Falha da ventoinha normalizada", level="ok")


def toggle_system_failure(session_state: Any) -> None:
    session_state.system_failure = not session_state.system_failure
    if session_state.system_failure:
        add_event(session_state, "Falha crítica do sistema acionada", level="alert")
    else:
        add_event(session_state, "Sistema crítico normalizado", level="ok")


def reset_system(session_state: Any) -> None:
    session_state.fan_failure = False
    session_state.system_failure = False
    session_state.thermal_alert = "none"
    add_event(session_state, "Reset geral executado", level="ok")


def update_pwm_user(session_state: Any, slider_value: int) -> None:
    """Update pwm_user value based on slider input (0-100 -> 0-200)."""
    pwm_output = slider_value * 2
    session_state.pwm_user = pwm_output
    session_state.pwm_slider_value = slider_value
    
    add_event(
        session_state, 
        f"PWM Manual: {slider_value}% → {pwm_output} (2x)", 
        level="info"
    )
    logger.info(f"update_pwm_user -> slider={slider_value}%, pwm_user={pwm_output}")


def build_snapshot(session_state: Any) -> dict[str, Any]:
    latest_pwm = session_state.history["pwm"][-1]
    latest_temp = session_state.history["temp"][-1]
    state_label, state_tone = compute_system_state(session_state)

    return {
        "latest_pwm": latest_pwm,
        "latest_temp": latest_temp,
        "setpoint": SETPOINT_C,
        "lamp_on": session_state.lamp_on,
        "state_label": state_label,
        "state_tone": state_tone,
        "status_text": status_text(session_state),
        "backend_state": compute_backend_state(session_state),
    }
