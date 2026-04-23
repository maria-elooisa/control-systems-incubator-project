import numpy as np
import plotly.graph_objects as go


def init_history(history_size: int = 50) -> dict:
    """Create simulated initial data for PWM and temperature history."""
    x = np.arange(history_size)
    pwm = np.random.uniform(40, 70, history_size)
    temp = 37 + np.random.normal(0, 0.3, history_size)

    return {
        "x": x.tolist(),
        "pwm": pwm.tolist(),
        "temp": temp.tolist(),
    }


def append_sample(history: dict, fan_failure: bool, system_failure: bool) -> dict:
    """Append one new sample while keeping a fixed-size history."""
    next_x = history["x"][-1] + 1 if history["x"] else 0

    if system_failure:
        next_pwm = 0.0
        next_temp = max(20.0, history["temp"][-1] - np.random.uniform(0.1, 0.3))
    elif fan_failure:
        next_pwm = np.random.uniform(60, 95)
        next_temp = history["temp"][-1] + np.random.uniform(0.02, 0.12)
    else:
        next_pwm = np.random.uniform(40, 70)
        target_temp = 37.0
        next_temp = history["temp"][-1] + np.random.uniform(-0.08, 0.08)
        next_temp += (target_temp - next_temp) * 0.15

    history["x"].append(float(next_x))
    history["pwm"].append(float(next_pwm))
    history["temp"].append(float(next_temp))

    for key in ("x", "pwm", "temp"):
        history[key] = history[key][-50:]

    return history


def build_figure(history: dict) -> go.Figure:
    """Build Plotly figure with PWM and temperature."""
    fig = go.Figure()

    fig.add_scatter(
        x=history["x"],
        y=history["pwm"],
        mode="lines",
        name="PWM (%)",
        line={"color": "#F28C28", "width": 3},
        yaxis="y1",
    )

    fig.add_scatter(
        x=history["x"],
        y=history["temp"],
        mode="lines",
        name="Temperatura (°C)",
        line={"color": "#D62828", "width": 3},
        yaxis="y2",
    )

    fig.update_layout(
        margin={"l": 20, "r": 20, "t": 15, "b": 15},
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend={"orientation": "h", "y": 1.1, "x": 0.0},
        xaxis={"title": "Amostras", "showgrid": True, "gridcolor": "#F2F2F2"},
        yaxis={"title": "PWM (%)", "range": [0, 100], "showgrid": False},
        yaxis2={
            "title": "Temperatura (°C)",
            "overlaying": "y",
            "side": "right",
            "range": [34, 41],
            "showgrid": False,
        },
    )

    return fig
