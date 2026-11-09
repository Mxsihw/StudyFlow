import unittest

from fastapi.testclient import TestClient

from api.main import app


class TestApiFoundation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_swagger_docs_are_available(self):
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_includes_health(self):
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/health", response.json()["paths"])
