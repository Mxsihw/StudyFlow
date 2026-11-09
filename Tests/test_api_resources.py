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


class TestResourcesApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)
        self.course_id = services.create_course("Algorithms")

    def test_list_resources(self):
        beta_id = services.create_resource("Beta", "Book")
        alpha_id = services.create_resource("Alpha", "Article")

        response = self.client.get("/resources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [resource["id"] for resource in response.json()],
            [alpha_id, beta_id],
        )

    def test_list_resources_filters_by_course(self):
        other_course_id = services.create_course("Databases")
        first_id = services.create_resource(
            "Algorithms notes",
            "Notes",
            course_id=self.course_id,
        )
        services.create_resource(
            "Databases notes",
            "Notes",
            course_id=other_course_id,
        )
        services.create_resource("Unassigned notes", "Notes")

        response = self.client.get(
            "/resources",
            params={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [resource["id"] for resource in response.json()],
            [first_id],
        )
        self.assertEqual(
            response.json()[0]["course_id"],
            self.course_id,
        )

    def test_get_existing_resource(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
            course_id=self.course_id,
            author="Ada",
            category="Lecture",
            url="https://example.com/notes",
            status="In Progress",
            notes="Chapter 1",
        )

        response = self.client.get(f"/resources/{resource_id}")

        self.assertEqual(response.status_code, 200)

        resource = response.json()
        self.assertEqual(resource["id"], resource_id)
        self.assertEqual(resource["course_id"], self.course_id)
        self.assertEqual(resource["title"], "Algorithms notes")
        self.assertEqual(resource["resource_type"], "Notes")
        self.assertEqual(resource["author"], "Ada")
        self.assertEqual(resource["category"], "Lecture")
        self.assertEqual(
            resource["url"],
            "https://example.com/notes",
        )
        self.assertEqual(resource["status"], "In Progress")
        self.assertEqual(resource["notes"], "Chapter 1")
        self.assertIsInstance(resource["created_at"], str)

    def test_get_missing_resource_returns_404(self):
        response = self.client.get("/resources/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Resource not found.",
                }
            },
        )

    def test_create_resource(self):
        payload = {
            "title": "Algorithms notes",
            "resource_type": "Notes",
            "course_id": self.course_id,
            "author": "Ada",
            "category": "Lecture",
            "url": "https://example.com/notes",
            "status": "In Progress",
            "notes": "Chapter 1",
        }

        response = self.client.post("/resources", json=payload)

        self.assertEqual(response.status_code, 201)

        resource = response.json()
        self.assertIsInstance(resource["id"], int)
        self.assertIsInstance(resource["created_at"], str)
        self.assertEqual(
            {
                key: resource[key]
                for key in payload
            },
            payload,
        )

        get_response = self.client.get(
            f"/resources/{resource['id']}"
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), resource)

    def test_create_resource_uses_defaults(self):
        response = self.client.post(
            "/resources",
            json={
                "title": "Algorithms notes",
                "resource_type": "Notes",
            },
        )

        self.assertEqual(response.status_code, 201)

        resource = response.json()
        self.assertEqual(resource["status"], "Not Started")
        self.assertIsNone(resource["course_id"])
        self.assertIsNone(resource["author"])
        self.assertIsNone(resource["category"])
        self.assertIsNone(resource["url"])
        self.assertIsNone(resource["notes"])

    def test_create_resource_missing_title_returns_422(self):
        response = self.client.post(
            "/resources",
            json={"resource_type": "Notes"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_resource_missing_type_returns_422(self):
        response = self.client.post(
            "/resources",
            json={"title": "Algorithms notes"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_resource_with_blank_title_returns_400(self):
        response = self.client.post(
            "/resources",
            json={
                "title": "   ",
                "resource_type": "Notes",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": "Resource title cannot be empty.",
                }
            },
        )

    def test_create_resource_for_missing_course_returns_409(self):
        response = self.client.post(
            "/resources",
            json={
                "title": "Orphan notes",
                "resource_type": "Notes",
                "course_id": 999999,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_partial_update_preserves_untouched_fields(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
            course_id=self.course_id,
            author="Ada",
            category="Lecture",
            url="https://example.com/notes",
            status="Not Started",
            notes="Chapter 1",
        )

        response = self.client.patch(
            f"/resources/{resource_id}",
            json={"title": "Advanced notes", "status": "Completed"},
        )

        self.assertEqual(response.status_code, 200)

        resource = response.json()
        self.assertEqual(resource["title"], "Advanced notes")
        self.assertEqual(resource["status"], "Completed")
        self.assertEqual(resource["course_id"], self.course_id)
        self.assertEqual(resource["resource_type"], "Notes")
        self.assertEqual(resource["author"], "Ada")
        self.assertEqual(resource["category"], "Lecture")
        self.assertEqual(
            resource["url"],
            "https://example.com/notes",
        )
        self.assertEqual(resource["notes"], "Chapter 1")

    def test_update_missing_resource_returns_404(self):
        response = self.client.patch(
            "/resources/999999",
            json={"title": "Missing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_resource(self):
        resource_id = services.create_resource(
            "To Delete",
            "Notes",
        )

        response = self.client.delete(
            f"/resources/{resource_id}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(
            f"/resources/{resource_id}"
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_resource_returns_404(self):
        response = self.client.delete("/resources/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Resource not found.",
                }
            },
        )

    def test_list_resource_tags(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )
        beta_id = services.create_tag("Beta")
        alpha_id = services.create_tag("Alpha")
        services.add_tag_to_resource(resource_id, beta_id)
        services.add_tag_to_resource(resource_id, alpha_id)

        response = self.client.get(
            f"/resources/{resource_id}/tags"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": alpha_id, "name": "Alpha"},
                {"id": beta_id, "name": "Beta"},
            ],
        )

    def test_list_resource_tags_for_missing_resource_returns_404(self):
        response = self.client.get("/resources/999999/tags")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_add_tag_to_resource(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )
        tag_id = services.create_tag("Important")

        response = self.client.post(
            f"/resources/{resource_id}/tags/{tag_id}"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {"id": tag_id, "name": "Important"},
        )

        list_response = self.client.get(
            f"/resources/{resource_id}/tags"
        )

        self.assertEqual(
            list_response.json(),
            [{"id": tag_id, "name": "Important"}],
        )

    def test_add_existing_tag_to_resource_is_idempotent(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )
        tag_id = services.create_tag("Important")
        services.add_tag_to_resource(resource_id, tag_id)

        response = self.client.post(
            f"/resources/{resource_id}/tags/{tag_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": tag_id, "name": "Important"},
        )

        list_response = self.client.get(
            f"/resources/{resource_id}/tags"
        )

        self.assertEqual(len(list_response.json()), 1)

    def test_add_tag_to_missing_resource_returns_404(self):
        tag_id = services.create_tag("Important")

        response = self.client.post(
            f"/resources/999999/tags/{tag_id}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_add_missing_tag_to_resource_returns_404(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )

        response = self.client.post(
            f"/resources/{resource_id}/tags/999999"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_remove_tag_from_resource(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )
        tag_id = services.create_tag("Important")
        services.add_tag_to_resource(resource_id, tag_id)

        response = self.client.delete(
            f"/resources/{resource_id}/tags/{tag_id}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        list_response = self.client.get(
            f"/resources/{resource_id}/tags"
        )

        self.assertEqual(list_response.json(), [])

    def test_remove_absent_tag_from_resource_is_idempotent(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )
        tag_id = services.create_tag("Important")

        first = self.client.delete(
            f"/resources/{resource_id}/tags/{tag_id}"
        )
        second = self.client.delete(
            f"/resources/{resource_id}/tags/{tag_id}"
        )

        self.assertEqual(first.status_code, 204)
        self.assertEqual(second.status_code, 204)

    def test_remove_tag_from_missing_resource_returns_404(self):
        tag_id = services.create_tag("Important")

        response = self.client.delete(
            f"/resources/999999/tags/{tag_id}"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_remove_missing_tag_from_resource_returns_404(self):
        resource_id = services.create_resource(
            "Algorithms notes",
            "Notes",
        )

        response = self.client.delete(
            f"/resources/{resource_id}/tags/999999"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )
