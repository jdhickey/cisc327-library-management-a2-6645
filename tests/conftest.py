import subprocess
import time
import os
import sys
import signal
import pytest
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

@pytest.fixture(scope="session")
def live_server():
    proc = subprocess.Popen(
        ["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    # Wait until it responds
    url = "http://127.0.0.1:5000"
    for _ in range(20):
        try:
            requests.get(url)
            break
        except Exception:
            time.sleep(0.5)
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        raise RuntimeError("Flask app did not start")

    yield url

    # Kill Flask server when tests finish
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)