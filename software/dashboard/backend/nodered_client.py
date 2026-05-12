"""HTTP client for sending PWM values to Node-RED."""

from __future__ import annotations

import urllib.request
import urllib.error
import json
from datetime import datetime

# ── Configuração ──────────────────────────────────────────────────────────────
NODE_RED_HOST = "http://localhost"
NODE_RED_PORT = 1880
NODE_RED_ENDPOINT = "/pwm"          # ajuste para a rota configurada no Node-RED
TIMEOUT_S = 3.0
# ─────────────────────────────────────────────────────────────────────────────


def _node_red_url() -> str:
    return f"{NODE_RED_HOST}:{NODE_RED_PORT}{NODE_RED_ENDPOINT}"


def send_pwm(pwm_value: float) -> dict:
    """
    POST { "pwm": <percentual> } para o Node-RED.

    Retorna dict com: ok, status_code, message, timestamp.
    """
    payload = json.dumps({"pwm": round(pwm_value, 2)}).encode("utf-8")
    url = _node_red_url()
    timestamp = datetime.now().strftime("%H:%M:%S")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return {
                "ok": True,
                "status_code": resp.status,
                "message": f"PWM {pwm_value:.1f}% enviado com sucesso",
                "timestamp": timestamp,
            }

    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": exc.code,
            "message": f"Erro HTTP {exc.code}: {exc.reason}",
            "timestamp": timestamp,
        }

    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status_code": None,
            "message": f"Node-RED inacessível: {str(exc.reason)}",
            "timestamp": timestamp,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status_code": None,
            "message": f"Erro inesperado: {exc}",
            "timestamp": timestamp,
        }
