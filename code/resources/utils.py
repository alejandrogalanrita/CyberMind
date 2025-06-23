import requests

def send_log(level, user, message):
    payload = {
        "level": level,
        "user": user,
        "message": message
    }
    requests.post("http://host.docker.internal:3330/log", json=payload)