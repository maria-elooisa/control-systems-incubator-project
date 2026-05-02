from __future__ import annotations

from time import monotonic
from datetime import datetime
from pathlib import Path
from typing import Any
from backend.data_source import get_telemetry

from components.pwm_plot import append_sample, init_history

SETPOINT_C = 37.0
TEMP_MIN_CRITICAL_C = 30.0
TEMP_MAX_CRITICAL_C = 40.0
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


def init_dashboard_state(session_state: Any) -> None:
    if "history" not in session_state:
        session_state.history = init_history(history_size=50)

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


def add_event(session_state: Any, message: str, level: str = "info") -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    session_state.events.insert(0, {"time": timestamp, "message": message, "level": level})
    session_state.events = session_state.events[:6]


def tick(session_state: Any) -> None:
    data = get_telemetry()

    temp = data["temp"]
    pwm = data["pwm"]

    session_state.history["x"].append(session_state.history["x"][-1] + 1)
    session_state.history["temp"].append(temp)
    session_state.history["pwm"].append(pwm)

    for key in ("x", "pwm", "temp"):
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
    """Resolve image state from the same logic used by system status."""
    latest_temp = session_state.history["temp"][-1]

    if latest_temp < TEMP_MIN_CRITICAL_C:
        return "frio"
    if latest_temp > TEMP_MAX_CRITICAL_C:
        return "calor"

    if session_state.system_failure or session_state.fan_failure:
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


def build_snapshot(session_state: Any) -> dict[str, Any]:
    latest_pwm = session_state.history["pwm"][-1]
    latest_temp = session_state.history["temp"][-1]
    state_label, state_tone = compute_system_state(session_state)

    return {
        "latest_pwm": latest_pwm,
        "latest_temp": latest_temp,
        "setpoint": SETPOINT_C,
        "state_label": state_label,
        "state_tone": state_tone,
        "status_text": status_text(session_state),
        "backend_state": compute_backend_state(session_state),
    }
