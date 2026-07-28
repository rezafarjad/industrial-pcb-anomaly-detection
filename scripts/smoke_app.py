"""Start Streamlit, verify its health endpoint, and shut it down."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def main() -> int:
    port = _available_port()
    url = f"http://127.0.0.1:{port}/_stcore/health"
    environment = os.environ.copy()
    environment["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ROOT / "streamlit_app.py"),
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    creation_flags = (
        subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creation_flags,
    )
    healthy = False
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.status == 200 and response.read().strip() == b"ok":
                        healthy = True
                        break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.25)

        if not healthy:
            output = process.stdout.read() if process.stdout is not None else ""
            print(output[-4000:], file=sys.stderr)
            print("Streamlit health check failed.", file=sys.stderr)
            return 1
        print(f"Streamlit health check passed on port {port}.")
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
