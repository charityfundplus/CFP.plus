import unittest
from email.message import Message
from io import BytesIO
from types import SimpleNamespace
from urllib.request import BaseHandler, build_opener
from urllib.response import addinfourl

from nvidia_readiness import NoRedirect, readiness, sdk_status, service_status


class FixtureTransport(BaseHandler):
    handler_order = 100

    def __init__(self, status):
        self.status = status
        self.requests = []

    def https_open(self, request):
        self.requests.append((request.get_method(), request.full_url))
        headers = Message()
        if self.status == 302:
            headers["Location"] = "https://unexpected.invalid/"
        response = addinfourl(BytesIO(), headers, request.full_url, self.status)
        response.msg = "fixture"
        return response

class ReadinessTest(unittest.TestCase):
    def test_sdk_import(self):
        self.assertEqual(
            sdk_status("cudaq", load_module=lambda name: SimpleNamespace(__version__="test")),
            {"status": "imported", "version": "test"},
        )

    def test_sdk_missing_dependency(self):
        def load_module(name):
            raise ModuleNotFoundError(name="cupy")

        self.assertEqual(sdk_status("cuquantum", load_module=load_module),
                         {"status": "dependency_unavailable"})

    def test_unconfigured_endpoints(self):
        result = readiness({})
        self.assertEqual(result["nim"], {"status": "not_configured"})
        self.assertEqual(result["ace_audio2face"], {"status": "not_configured"})

    def test_reject_invalid_origins(self):
        for origin in ("http://example.com", "https://user@example.com",
                       "https://localhost:bad", "https://localhost/path",
                       "https://localhost?token=test"):
            with self.subTest(origin=origin):
                self.assertEqual(service_status(origin), {"status": "invalid_origin"})

    def test_http_readiness_and_no_redirect(self):
        origin = "https://fixture.invalid"
        for code, expected in ((200, "ready"), (503, "not_ready"), (302, "not_ready")):
            with self.subTest(code=code):
                transport = FixtureTransport(code)
                result = service_status(origin, opener=build_opener(transport, NoRedirect()))
                self.assertEqual(result, {"status": expected, "http_status": code})
                self.assertEqual(transport.requests, [("GET", origin + "/v1/health/ready")])

    def test_origin_boundary_rejects_ambiguous_and_non_origin_urls(self):
        origins = (
            " https://example.com", "https://example.com\n",
            "https://ex\tample.com", "https://example.com?",
            "https://example.com#", "https://example.com:",
            "https://example.com:65536", "https://example.com:00443",
            "https://user:pass@example.com", "https://example.com\\@localhost",
            "https://example.com/%2e%2e", "https://example.com//",
            "https://example%2ecom", "https://example.com.",
            "https://-example.com", "https://example..com",
            "https://169.254.169.254", "https://2130706433",
            "https://0x7f000001", "https://127.1",
            "https://[::ffff:127.0.0.1]", "https://[::1%25zone]",
        )
        for origin in origins:
            with self.subTest(origin=origin):
                self.assertEqual(
                    service_status(origin, opener=object()),
                    {"status": "invalid_origin"},
                )


class SocketReadinessTest(unittest.TestCase):
    def test_readiness_over_tcp(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread

        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response(self.server.response_status)
                if self.server.response_status == 302:
                    self.send_header("Location", "/redirect-target")
                self.end_headers()

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                for status in (200, 503, 302):
                    server.response_status = status
                    with self.subTest(status=status):
                        self.assertEqual(
                            service_status(origin),
                            {
                                "status": "ready" if status == 200 else "not_ready",
                                "http_status": status,
                            },
                        )
            finally:
                server.shutdown()
                worker.join()

        self.assertEqual(calls, ["/v1/health/ready"] * 3)
