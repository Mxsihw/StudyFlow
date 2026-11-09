import unittest

from fastapi.testclient import TestClient

import database
import services
from Tests.db_test_utils import create_test_schema, drop_test_schema
from api.main import app


_TEST_DB_SCHEMA = None
_ORIGINAL_DB_URL = None


def setUpModule():
    global _TEST_DB_SCHEMA
    global _ORIGINAL_DB_URL

    _ORIGINAL_DB_URL = database.get_database_url()
    test_url, _TEST_DB_SCHEMA = create_test_schema()

    database.configure_database(test_url)
    database.initialize_database()


def tearDownModule():
    global _TEST_DB_SCHEMA
    global _ORIGINAL_DB_URL

    if _ORIGINAL_DB_URL is not None:
        database.configure_database(_ORIGINAL_DB_URL)

    if _TEST_DB_SCHEMA is not None:
        drop_test_schema(_TEST_DB_SCHEMA)

    _TEST_DB_SCHEMA = None
    _ORIGINAL_DB_URL = None


def reset_database():
    connection = database.get_connection()

    try:
        connection.execute("""
            TRUNCATE TABLE
                resource_tags,
                resources,
                assignments,
                study_sessions,
                calendar_events,
                tags,
                courses,
                user_preferences,
                users
            RESTART IDENTITY CASCADE
        """)
        connection.commit()

    finally:
        connection.close()


class TestTagsApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)

    def test_list_tags(self):
        beta_id = services.create_tag("Beta")
        alpha_id = services.create_tag("Alpha")

        response = self.client.get("/tags")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": alpha_id, "name": "Alpha"},
                {"id": beta_id, "name": "Beta"},
            ],
        )

    def test_get_existing_tag(self):
        tag_id = services.create_tag("Important")

        response = self.client.get(f"/tags/{tag_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": tag_id, "name": "Important"},
        )

    def test_get_missing_tag_returns_404(self):
        response = self.client.get("/tags/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Tag not found.",
                }
            },
        )

    def test_create_tag(self):
        response = self.client.post(
            "/tags",
            json={"name": "Important"},
        )

        self.assertEqual(response.status_code, 201)

        tag = response.json()
        self.assertIsInstance(tag["id"], int)
        self.assertEqual(tag["name"], "Important")

        get_response = self.client.get(f"/tags/{tag['id']}")

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), tag)

    def test_create_tag_missing_name_returns_422(self):
        response = self.client.post("/tags", json={})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_tag_with_blank_name_returns_400(self):
        response = self.client.post(
            "/tags",
            json={"name": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": "Tag name cannot be empty.",
                }
            },
        )

    def test_create_duplicate_tag_returns_409(self):
        services.create_tag("Important")

        response = self.client.post(
            "/tags",
            json={"name": "Important"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_update_tag(self):
        tag_id = services.create_tag("Old Name")

        response = self.client.patch(
            f"/tags/{tag_id}",
            json={"name": "New Name"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": tag_id, "name": "New Name"},
        )

    def test_empty_update_returns_current_tag(self):
        tag_id = services.create_tag("Important")

        response = self.client.patch(f"/tags/{tag_id}", json={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": tag_id, "name": "Important"},
        )

    def test_update_missing_tag_returns_404(self):
        response = self.client.patch(
            "/tags/999999",
            json={"name": "Missing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_update_tag_with_blank_name_returns_400(self):
        tag_id = services.create_tag("Important")

        response = self.client.patch(
            f"/tags/{tag_id}",
            json={"name": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_delete_tag(self):
        tag_id = services.create_tag("To Delete")

        response = self.client.delete(f"/tags/{tag_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(f"/tags/{tag_id}")

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_tag_returns_404(self):
        response = self.client.delete("/tags/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Tag not found.",
                }
            },
        )
