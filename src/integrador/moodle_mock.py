import json
import logging
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from django.conf import settings


logger = logging.getLogger(__name__)


class MockHTTPResponse:
    def __init__(self, payload: object, status_code: int = 200, headers: dict | None = None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.reason = HTTPStatus(status_code).phrase
        self.headers = headers or {"Content-Type": "application/json"}
        self.content = json.dumps(payload).encode("utf-8")


class MoodleHTTPMock:
    """Mock HTTP client for Moodle local/suap endpoints used by integrador."""

    def _extract_service(self, url: str) -> str:
        query = urlparse(url).query
        if not query:
            return ""
        first_token = query.split("&", 1)[0]
        return first_token.split("=", 1)[0]

    def _extract_query_params(self, url: str) -> dict[str, str]:
        query = urlparse(url).query
        return {key: values[0] for key, values in parse_qs(query).items() if values}

    def request(self, method: str, url: str, jsonbody: dict | None = None) -> MockHTTPResponse:
        parsed = urlparse(url)
        if not parsed.path.endswith("/local/suap/api/index.php"):
            return MockHTTPResponse({"error": "Endpoint Moodle mock não reconhecido."}, status_code=404)

        service = self._extract_service(url)
        if method == "POST" and service == "sync_up_enrolments":
            payload = jsonbody or {}
            return MockHTTPResponse(
                {
                    "status": "success",
                    "mock": True,
                    "url": f"{parsed.scheme}://{parsed.netloc}/course/view.php?id=1",
                    "cohort_count": len(payload.get("coortes", [])),
                }
            )

        if method == "GET" and service == "sync_down_grades":
            params = self._extract_query_params(url)
            diario_id = params.get("diario_id", "")
            return MockHTTPResponse(
                [
                    {
                        "matricula": "20260001",
                        "nota": 8.5,
                        "diario_id": diario_id,
                        "mock": True,
                    }
                ]
            )

        return MockHTTPResponse({"error": f"Serviço não suportado no mock: {service}"}, status_code=400)

    def get(self, url: str) -> MockHTTPResponse:
        return self.request("GET", url)

    def post(self, url: str, jsonbody: dict | None = None) -> MockHTTPResponse:
        return self.request("POST", url, jsonbody=jsonbody)


_server_lock = threading.Lock()
_server = None
_server_thread = None


def start_mock_moodle_server_in_background() -> None:
    """Start a lightweight HTTP server serving mocked Moodle endpoints."""
    global _server
    global _server_thread

    if not getattr(settings, "MOODLE_HTTP_MOCK_BACKGROUND", False):
        return

    with _server_lock:
        if _server_thread is not None and _server_thread.is_alive():
            return

        host = getattr(settings, "MOODLE_HTTP_MOCK_HOST", "127.0.0.1")
        port = int(getattr(settings, "MOODLE_HTTP_MOCK_PORT", 18091))
        mock = MoodleHTTPMock()

        class Handler(BaseHTTPRequestHandler):
            def _write_response(self, response: MockHTTPResponse):
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response.content)

            def do_GET(self):
                response = mock.get(self.path)
                self._write_response(response)

            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                response = mock.post(self.path, jsonbody=body)
                self._write_response(response)

            def log_message(self, format, *args):
                logger.debug("moodle-mock: " + format, *args)

        _server = ThreadingHTTPServer((host, port), Handler)
        _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
        _server_thread.start()
        logger.info("Moodle mock HTTP server running on %s:%s", host, port)
