"""Live smoke test for the NiceGUI interface server.

Starts the server in a subprocess, checks the catalog and a wizard page respond,
then shuts it down. Skips when NiceGUI is not installed.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

pytest.importorskip("nicegui")


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def test_web_server_serves_catalog_and_wizard(tmp_path):
    port = _free_port()
    runner = tmp_path / "run_server.py"
    runner.write_text(
        "from verigen.ui.app import launch\n"
        f"launch(show=False, native=False, port={port}, reload=False)\n",
        encoding="utf-8",
    )
    log = tmp_path / "server.log"
    log_handle = log.open("w", encoding="utf-8")
    # NiceGUI switches into its internal screen-test mode if it sees pytest env
    # vars; scrub them so the child runs as a normal server.
    child_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("PYTEST") and not k.startswith("NICEGUI")
    }
    proc = subprocess.Popen(
        [sys.executable, str(runner)],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        cwd=str(tmp_path),
        env=child_env,
    )
    try:
        body = None
        deadline = time.time() + 30
        while time.time() < deadline:
            if proc.poll() is not None:
                log_handle.flush()
                pytest.fail(
                    "web server exited early:\n" + log.read_text(encoding="utf-8")
                )
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as resp:
                    if resp.status == 200:
                        body = resp.read().decode("utf-8", "replace")
                        break
            except Exception:
                time.sleep(0.5)
        assert body is not None, "server did not become ready in time"
        assert "VeriGen" in body
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/g/synchronizer", timeout=5
        ) as resp2:
            assert resp2.status == 200
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        log_handle.close()
