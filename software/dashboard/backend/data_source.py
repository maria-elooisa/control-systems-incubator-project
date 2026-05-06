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

    import os
    import logging
    import random
    import urllib.parse
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    # allow overriding target URL and SSL verify via environment for flexibility
    NODE_RED_URL = os.getenv("NODE_RED_URL", "http://localhost:1880/data")
    NODE_RED_VERIFY = os.getenv("NODE_RED_VERIFY", "true").lower() in ("1", "true", "yes")

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

        logger.info("get_telemetry (mock) -> temp=%.2f, pwm=%.1f", _mock_temp, _mock_pwm)
        return {"temp": _mock_temp, "pwm": _mock_pwm}


    # prepare a requests session with a small retry policy so transient errors don't block
    _session = requests.Session()
    retries = Retry(total=2, backoff_factor=0.25, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retries)
    _session.mount("http://", adapter)
    _session.mount("https://", adapter)


    def get_telemetry():
        parsed = urllib.parse.urlparse(NODE_RED_URL)
        logger.debug("get_telemetry -> url=%s scheme=%s netloc=%s", NODE_RED_URL, parsed.scheme, parsed.netloc)

        try:
            # use short connect/read timeouts so UI doesn't hang; tuple = (connect, read)
            response = _session.get(NODE_RED_URL, timeout=(0.6, 1.0), verify=NODE_RED_VERIFY)
            logger.debug("get_telemetry -> status=%s elapsed=%s", response.status_code, getattr(response, "elapsed", None))

            # raise for HTTP error statuses so we can handle them explicitly
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                logger.warning("get_telemetry -> invalid JSON response, using mock")
                return _mock_telemetry()

            # validação básica
            if data is None:
                logger.warning("get_telemetry -> received None, returning zeros")
                return {"temp": 0, "pwm": 0}

            # log do payload recebido para debug no terminal (detalhado)
            logger.debug("get_telemetry payload -> %s", data)
            logger.info("get_telemetry -> temp=%s, pwm=%s", data.get("temp"), data.get("pwm"))

            # garante que tem as chaves certas
            return {
                "temp": data.get("temp", 0),
                "pwm": data.get("pwm", 0),
            }

        except requests.exceptions.SSLError:
            logger.exception("get_telemetry -> SSL error when contacting %s", NODE_RED_URL)
            return _mock_telemetry()
        except requests.exceptions.Timeout:
            logger.warning("get_telemetry -> timeout contacting %s", NODE_RED_URL)
            return _mock_telemetry()
        except requests.exceptions.RequestException:
            # register full exception trace so we can diagnose failures contacting Node-RED
            logger.exception("get_telemetry failed, using internal mock telemetry")
            return _mock_telemetry()