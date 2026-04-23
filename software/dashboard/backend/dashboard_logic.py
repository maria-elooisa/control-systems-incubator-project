from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from components.pwm_plot import append_sample, init_history

SETPOINT_C = 37.0


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
        session_state.automatic_process = False

    if "events" not in session_state:
        session_state.events = []
        add_event(session_state, "Dashboard iniciado", level="ok")


def add_event(session_state: Any, message: str, level: str = "info") -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    session_state.events.insert(0, {"time": timestamp, "message": message, "level": level})
    session_state.events = session_state.events[:6]


def tick(session_state: Any) -> None:
    session_state.history = append_sample(
        session_state.history,
        fan_failure=session_state.fan_failure,
        system_failure=session_state.system_failure,
    )


def compute_system_state(session_state: Any) -> tuple[str, str]:
    if session_state.system_failure:
        return "Alerta", "alert"
    if session_state.fan_failure:
        return "Alerta", "warn"
    return "Normal", "ok"


def compute_backend_state(history: dict[str, list[float]]) -> str:
    latest_temp = history["temp"][-1]
    if latest_temp < 36.8:
        return "frio"
    if latest_temp > 37.2:
        return "calor"
    return "ideal"


def status_text(session_state: Any) -> str:
    if session_state.system_failure:
        return "Falha Crítica"
    if session_state.fan_failure:
        return "Falha Ventoinha"
    return "Sistema Estável"


def toggle_fan_failure(session_state: Any) -> None:
    session_state.automatic_process = False
    session_state.fan_failure = not session_state.fan_failure
    if session_state.fan_failure:
        add_event(session_state, "Falha da ventoinha acionada", level="warn")
    else:
        add_event(session_state, "Falha da ventoinha normalizada", level="ok")


def toggle_system_failure(session_state: Any) -> None:
    session_state.automatic_process = False
    session_state.system_failure = not session_state.system_failure
    if session_state.system_failure:
        add_event(session_state, "Falha crítica do sistema acionada", level="alert")
    else:
        add_event(session_state, "Sistema crítico normalizado", level="ok")


def reset_system(session_state: Any) -> None:
    session_state.automatic_process = False
    session_state.fan_failure = False
    session_state.system_failure = False
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
        "backend_state": compute_backend_state(session_state.history),
    }
