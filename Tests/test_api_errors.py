import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import IntegrityError

from api.errors import register_exception_handlers
from api.main import app
from validators import ValidationError


def create_error_test_app():
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/validation-error")
    def raise_validation_error():
        raise ValidationError("Course name cannot be empty.")

    @test_app.get("/integrity-error")
    def raise_integrity_error():
        raise IntegrityError(
            "duplicate key value violates unique constraint"
        )

    @test_app.get("/unexpected-error")
    def raise_unexpected_error():
        raise RuntimeError("secret internal detail")

    @test_app.get("/requires-query")
    def requires_query(value: int):
        return {"value": value}

    return test_app


class TestApiErrorResponses(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(
            create_error_test_app(),
            raise_server_exceptions=False,
        )

    def test_validation_error_returns_400(self):
        response = self.client.get("/validation-error")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": "Course name cannot be empty.",
                }
            },
        )

    def test_integrity_error_returns_409_without_internal_details(self):
        response = self.client.get("/integrity-error")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "conflict")
        self.assertNotIn("duplicate key", response.text)

    def test_request_validation_error_returns_422(self):
        response = self.client.get("/requires-query")

        self.assertEqual(response.status_code, 422)

        error = response.json()["error"]
        self.assertEqual(error["code"], "request_validation_error")
        self.assertEqual(error["message"], "Request validation failed.")
        self.assertEqual(error["details"][0]["field"], "query.value")

    def test_unexpected_error_returns_generic_500(self):
        with self.assertLogs("api.errors", level="ERROR"):
            response = self.client.get("/unexpected-error")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )
        self.assertNotIn("secret internal detail", response.text)


class TestApiHttpErrors(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_unknown_route_returns_consistent_404(self):
        response = self.client.get("/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Not Found",
                }
            },
        )
