from datetime import datetime, timedelta

import numpy as np
import plotly.graph_objects as go


def init_history(history_size: int = 50) -> dict:
    """Create initial data for PWM and temperature history."""
    x = np.arange(history_size)
    # PWM inicia em zero e só muda via ação do usuário no slider.
    pwm = np.zeros(history_size)
    temp = 36.5 + np.random.normal(0, 0.9, history_size)
    temp = np.clip(temp, 15.0, 48.0)
    now = datetime.now()
    time = [now - timedelta(seconds=(history_size - idx - 1)) for idx in range(history_size)]

    return {
        "x": x.tolist(),
        "time": time,
        "pwm": pwm.tolist(),
        "temp": temp.tolist(),
    }


def append_sample(history: dict, temp=None, pwm=None, fan_failure=False, system_failure=False) -> dict:
    """Append one new sample while keeping a fixed-size history."""
    next_x = history["x"][-1] + 1 if history["x"] else 0
    next_time = datetime.now()

    if system_failure:
        next_pwm = 0.0
        next_temp = history["temp"][-1] - np.random.uniform(0.8, 1.8)
    elif fan_failure:
        next_pwm = np.random.uniform(60, 95)
        next_temp = history["temp"][-1] + np.random.uniform(0.25, 0.85)
    else:
        next_pwm = np.clip(history["pwm"][-1] + np.random.uniform(-16, 16), 20, 95)
        target_temp = 36.4 + np.random.uniform(-1.4, 0.8)
        next_temp = history["temp"][-1] + np.random.uniform(-0.9, 0.7)
        next_temp += (target_temp - next_temp) * 0.22

        if np.random.rand() < 0.14:
            next_temp -= np.random.uniform(3.5, 7.5)

        if np.random.rand() < 0.06:
            next_temp += np.random.uniform(1.8, 4.5)

    history["x"].append(float(next_x))
    history["time"].append(next_time)
    history["pwm"].append(float(next_pwm))
    history["temp"].append(float(np.clip(next_temp, 10.0, 50.0)))

    for key in ("x", "time", "pwm", "temp"):
        history[key] = history[key][-50:]

    return history


def _trim_history(history: dict, display_samples: int = 10) -> dict:
    return {
        key: (history[key][-display_samples:] if len(history.get(key, [])) > display_samples else history.get(key, []))
        for key in ("x", "time", "pwm", "temp")
    }


def build_pwm_figure(history: dict) -> go.Figure:
    """Build Plotly figure with PWM history only."""
    trimmed = _trim_history(history)
    fig = go.Figure()

    for level in (0, 25, 50, 75, 100):
        fig.add_hline(
            y=level,
            line_width=1,
            line_dash="dot",
            line_color="rgba(242, 140, 40, 0.45)",
        )

    fig.add_scatter(
        x=trimmed["time"],
        y=trimmed["pwm"],
        mode="lines",
        name="PWM (%)",
        line={"color": "#F28C28", "width": 3.4, "shape": "hv"},
        fill="tozeroy",
        fillcolor="rgba(242, 140, 40, 0.16)",
        yaxis="y1",
        showlegend=False,
    )

    fig.add_scatter(
        x=[trimmed["time"][-1]] if trimmed["time"] else [datetime.now()],
        y=[trimmed["pwm"][-1]] if trimmed["pwm"] else [0],
        mode="markers",
        marker={"size": 10, "color": "#F28C28", "line": {"color": "white", "width": 1.5}},
        name="PWM atual",
        yaxis="y1",
        showlegend=False,
    )

    fig.update_layout(
        margin={"l": 18, "r": 18, "t": 10, "b": 10},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        xaxis={
            "title": "Data e hora",
            "showgrid": True,
            "gridcolor": "#F2F2F2",
            "zeroline": False,
            "tickfont": {"size": 11},
            "type": "date",
            "tickformat": "%d/%m %H:%M:%S",
        },
        yaxis={
            "title": "PWM (%)",
            "range": [0, 100],
            "showgrid": True,
            "gridcolor": "rgba(242, 140, 40, 0.16)",
            "griddash": "dot",
            "tickfont": {"size": 11},
            "tickmode": "array",
            "tickvals": [0, 25, 50, 75, 100],
        },
        transition={"duration": 0},
        uirevision="static",
        height=300,
    )

    return fig


def build_temperature_figure(history: dict) -> go.Figure:
    """Build Plotly figure with temperature history only."""
    trimmed = _trim_history(history)
    fig = go.Figure()

    fig.add_scatter(
        x=trimmed["time"],
        y=trimmed["temp"],
        mode="lines",
        name="Temperatura (°C)",
        line={"color": "#D1491E", "width": 3, "shape": "spline", "smoothing": 0.8},
    )

    fig.add_scatter(
        x=[trimmed["time"][-1]] if trimmed["time"] else [datetime.now()],
        y=[trimmed["temp"][-1]] if trimmed["temp"] else [0],
        mode="markers",
        marker={"size": 9, "color": "#D1491E", "line": {"color": "white", "width": 1.5}},
        name="Temp. atual",
        showlegend=False,
    )

    fig.add_hrect(
        y0=36.7,
        y1=37.3,
        fillcolor="rgba(242, 140, 40, 0.14)",
        line_width=0,
        layer="below",
        annotation_text="Faixa ideal",
        annotation_position="top left",
        annotation_font={"size": 11, "color": "#8f5c20"},
    )

    fig.update_layout(
        margin={"l": 18, "r": 18, "t": 10, "b": 10},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        legend={
            "orientation": "h",
            "y": 1.1,
            "x": 0.0,
            "bgcolor": "rgba(255,255,255,0.7)",
            "bordercolor": "#ececec",
            "borderwidth": 1,
        },
        xaxis={
            "title": "Data e hora",
            "showgrid": True,
            "gridcolor": "#F2F2F2",
            "zeroline": False,
            "tickfont": {"size": 11},
            "type": "date",
            "tickformat": "%d/%m %H:%M:%S",
        },
        yaxis={
            "title": "Temperatura (°C)",
            "range": [30, 45],
            "tickvals": [30, 35, 40, 45],
            "showgrid": False,
            "tickfont": {"size": 11},
        },
        # disable long transition to avoid visual 'flicker' on frequent updates
        transition={"duration": 0},
        # preserve UI state (zoom/selection) across re-renders
        uirevision="static",
        # make the chart larger to improve visibility of micro-variations
        height=480,
    )

    return fig


def build_figure(history: dict) -> go.Figure:
    """Backward-compatible combined figure alias."""
    return build_temperature_figure(history)


def build_pwm_gauge(pwm_value: float) -> go.Figure:
    """Build radial gauge for current PWM."""
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pwm_value,
            number={"suffix": "%", "font": {"size": 30, "color": "#2b2b2b"}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#8c8c8c",
                    "tickmode": "array",
                    "tickvals": [0, 25, 50, 75, 100],
                    "ticktext": ["0", "25", "50", "75", "100"],
                },
                "bar": {"color": "#F28C28", "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#fff4df"},
                    {"range": [40, 75], "color": "#ffe3b5"},
                    {"range": [75, 100], "color": "#ffd092"},
                ],
                "threshold": {
                    "line": {"color": "#d62828", "width": 3},
                    "thickness": 0.8,
                    "value": 90,
                },
            },
        )
    )

    gauge.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="white",
        height=185,
    )
    return gauge
