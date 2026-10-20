"""A real slowly streamed response must not evade the total request deadline."""

import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from extraction_service.inference.errors import FailureKind, ModelTransportError
from extraction_service.inference.http import JsonHttpClient


def test_total_timeout_cancels_slow_body_and_client_remains_usable() -> None:
    paths: list[str] = []
    body = b'{"ok":true}'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            paths.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()

            try:
                if self.path == "/slow":
                    for byte in body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.04)
                else:
                    self.wfile.write(body)
            except BrokenPipeError, ConnectionResetError:
                pass

        def log_message(self, format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        worker.start()
        client = JsonHttpClient(f"http://127.0.0.1:{server.server_port}")

        try:
            with pytest.raises(ModelTransportError) as raised:
                client.get("slow", 0.15)

            result = client.get("fast", 2.0)
        finally:
            client.close()
            server.shutdown()
            worker.join(timeout=1)

    assert raised.value.evidence.kind is FailureKind.TIMEOUT
    assert raised.value.evidence.message == "Total request deadline exceeded"
    assert raised.value.evidence.duration_ms >= 100.0
    assert result.body == {"ok": True}
    assert paths == ["/slow", "/fast"]
