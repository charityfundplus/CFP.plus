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
