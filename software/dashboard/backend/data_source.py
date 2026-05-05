import requests
import logging
import random

NODE_RED_URL = "http://localhost:1880/data"

logger = logging.getLogger(__name__)

# simple persistent mock state so fallback data evolves over time
_mock_temp = 36.5
_mock_pwm = 55.0


def _mock_telemetry():
    global _mock_temp, _mock_pwm
    # pwm random walk
    _mock_pwm = max(20.0, min(95.0, _mock_pwm + random.uniform(-8, 8)))

    # temperature step towards a moving target with occasional spikes/dips
    target_temp = 36.4 + random.uniform(-1.4, 0.8)
    next_temp = _mock_temp + random.uniform(-0.9, 0.7)
    next_temp += (target_temp - next_temp) * 0.22

    if random.random() < 0.14:
        next_temp -= random.uniform(3.5, 7.5)
    if random.random() < 0.06:
        next_temp += random.uniform(1.8, 4.5)

    _mock_temp = float(max(10.0, min(50.0, next_temp)))

    logger.info(f"get_telemetry (mock) -> temp={_mock_temp:.2f}, pwm={_mock_pwm:.1f}")
    return {"temp": _mock_temp, "pwm": _mock_pwm}


def get_telemetry():
    try:
        response = requests.get(NODE_RED_URL, timeout=1)
        data = response.json()

        # validação básica
        if data is None:
            logger.info("get_telemetry -> received None, returning zeros")
            return {"temp": 0, "pwm": 0}

        # log do payload recebido para debug no terminal
        logger.info(f"get_telemetry -> {data}")

        # garante que tem as chaves certas
        return {
            "temp": data.get("temp", 0),
            "pwm": data.get("pwm", 0)
        }

    except Exception as exc:
        # don't raise; use internal mock telemetry so the UI can keep showing evolving data
        logger.warning(f"get_telemetry failed ({exc}), using internal mock telemetry", exc_info=False)
        return _mock_telemetry()