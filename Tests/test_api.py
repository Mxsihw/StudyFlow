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


class TestApiContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spec = app.openapi()

    def test_all_routers_are_registered(self):
        expected = {
            ("get", "/courses"),
            ("post", "/courses"),
            ("get", "/courses/{course_id}"),
            ("patch", "/courses/{course_id}"),
            ("delete", "/courses/{course_id}"),
            ("get", "/assignments"),
            ("post", "/assignments"),
            ("get", "/assignments/{assignment_id}"),
            ("patch", "/assignments/{assignment_id}"),
            ("delete", "/assignments/{assignment_id}"),
            ("get", "/resources"),
            ("post", "/resources"),
            ("get", "/resources/{resource_id}"),
            ("patch", "/resources/{resource_id}"),
            ("delete", "/resources/{resource_id}"),
            ("get", "/resources/{resource_id}/tags"),
            ("post", "/resources/{resource_id}/tags/{tag_id}"),
            ("delete", "/resources/{resource_id}/tags/{tag_id}"),
            ("get", "/tags"),
            ("post", "/tags"),
            ("get", "/tags/{tag_id}"),
            ("patch", "/tags/{tag_id}"),
            ("delete", "/tags/{tag_id}"),
            ("get", "/study-sessions"),
            ("post", "/study-sessions"),
            ("get", "/study-sessions/{session_id}"),
            ("patch", "/study-sessions/{session_id}"),
            ("delete", "/study-sessions/{session_id}"),
            ("get", "/calendar-events"),
            ("post", "/calendar-events"),
            ("get", "/calendar-events/{event_id}"),
            ("patch", "/calendar-events/{event_id}"),
            ("delete", "/calendar-events/{event_id}"),
        }

        actual = {
            (method, path)
            for path, operations in self.spec["paths"].items()
            for method in operations
        }

        self.assertTrue(expected <= actual)

    def test_relationship_creation_documents_201(self):
        operation = self.spec["paths"][
            "/resources/{resource_id}/tags/{tag_id}"
        ]["post"]

        self.assertIn("201", operation["responses"])
        self.assertEqual(
            operation["responses"]["201"]["content"][
                "application/json"
            ]["schema"]["$ref"],
            "#/components/schemas/TagResponse",
        )

    def test_validation_errors_use_error_envelope(self):
        for path, method in (
            ("/courses", "post"),
            ("/assignments", "post"),
            ("/resources", "post"),
            ("/tags", "post"),
            ("/study-sessions", "post"),
            ("/calendar-events", "post"),
        ):
            schema = self.spec["paths"][path][method]["responses"][
                "422"
            ]["content"]["application/json"]["schema"]

            self.assertEqual(
                schema["$ref"],
                "#/components/schemas/ErrorResponse",
                msg=f"{method.upper()} {path}",
            )
