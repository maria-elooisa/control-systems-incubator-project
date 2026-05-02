import requests

NODE_RED_URL = "http://localhost:1880/data"

def get_telemetry():
    try:
        response = requests.get(NODE_RED_URL, timeout=1)
        data = response.json()

        # validação básica
        if data is None:
            return {"temp": 0, "pwm": 0}

        # garante que tem as chaves certas
        return {
            "temp": data.get("temp", 0),
            "pwm": data.get("pwm", 0)
        }

    except:
        return {"temp": 0, "pwm": 0}