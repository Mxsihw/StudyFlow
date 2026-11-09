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


class TestAssignmentsApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)
        self.course_id = services.create_course("Algorithms")

    def test_list_assignments(self):
        later_id = services.create_assignment(
            self.course_id,
            "Later",
            deadline="2026-06-01",
        )
        sooner_id = services.create_assignment(
            self.course_id,
            "Sooner",
            deadline="2026-05-01",
        )
        undated_id = services.create_assignment(
            self.course_id,
            "Undated",
        )

        response = self.client.get("/assignments")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [assignment["id"] for assignment in response.json()],
            [sooner_id, later_id, undated_id],
        )

    def test_list_assignments_filters_by_course(self):
        other_course_id = services.create_course("Databases")
        first_id = services.create_assignment(
            self.course_id,
            "Algorithms homework",
        )
        services.create_assignment(
            other_course_id,
            "Databases homework",
        )

        response = self.client.get(
            "/assignments",
            params={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [assignment["id"] for assignment in response.json()],
            [first_id],
        )
        self.assertEqual(
            response.json()[0]["course_id"],
            self.course_id,
        )

    def test_get_existing_assignment(self):
        assignment_id = services.create_assignment(
            self.course_id,
            "Algorithms homework",
            description="Chapter 1",
            deadline="2026-05-01",
            status="In Progress",
            priority="High",
            progress=40,
        )

        response = self.client.get(
            f"/assignments/{assignment_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": assignment_id,
                "course_id": self.course_id,
                "title": "Algorithms homework",
                "description": "Chapter 1",
                "deadline": "2026-05-01",
                "status": "In Progress",
                "priority": "High",
                "progress": 40,
            },
        )

    def test_get_missing_assignment_returns_404(self):
        response = self.client.get("/assignments/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Assignment not found.",
                }
            },
        )

    def test_create_assignment(self):
        payload = {
            "course_id": self.course_id,
            "title": "Operating Systems homework",
            "description": "Scheduler exercise",
            "deadline": "2026-05-10",
            "status": "In Progress",
            "priority": "High",
            "progress": 25,
        }

        response = self.client.post("/assignments", json=payload)

        self.assertEqual(response.status_code, 201)

        assignment = response.json()
        self.assertIsInstance(assignment["id"], int)
        self.assertEqual(
            assignment,
            {"id": assignment["id"], **payload},
        )

        get_response = self.client.get(
            f"/assignments/{assignment['id']}"
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), assignment)

    def test_create_assignment_uses_defaults(self):
        response = self.client.post(
            "/assignments",
            json={
                "course_id": self.course_id,
                "title": "Reading",
            },
        )

        self.assertEqual(response.status_code, 201)

        assignment = response.json()
        self.assertEqual(assignment["status"], "Not Started")
        self.assertEqual(assignment["priority"], "Medium")
        self.assertEqual(assignment["progress"], 0)
        self.assertIsNone(assignment["description"])
        self.assertIsNone(assignment["deadline"])

    def test_create_assignment_missing_title_returns_422(self):
        response = self.client.post(
            "/assignments",
            json={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_assignment_with_blank_title_returns_400(self):
        response = self.client.post(
            "/assignments",
            json={
                "course_id": self.course_id,
                "title": "   ",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": "Assignment title cannot be empty.",
                }
            },
        )

    def test_create_assignment_with_invalid_deadline_returns_400(self):
        response = self.client.post(
            "/assignments",
            json={
                "course_id": self.course_id,
                "title": "Reading",
                "deadline": "not-a-date",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_create_assignment_for_missing_course_returns_409(self):
        response = self.client.post(
            "/assignments",
            json={
                "course_id": 999999,
                "title": "Orphan",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_partial_update_preserves_untouched_fields(self):
        assignment_id = services.create_assignment(
            self.course_id,
            "Algorithms homework",
            description="Chapter 1",
            deadline="2026-05-01",
            status="Not Started",
            priority="Medium",
            progress=10,
        )

        response = self.client.patch(
            f"/assignments/{assignment_id}",
            json={"title": "Advanced homework", "progress": 60},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": assignment_id,
                "course_id": self.course_id,
                "title": "Advanced homework",
                "description": "Chapter 1",
                "deadline": "2026-05-01",
                "status": "Not Started",
                "priority": "Medium",
                "progress": 60,
            },
        )

    def test_update_missing_assignment_returns_404(self):
        response = self.client.patch(
            "/assignments/999999",
            json={"title": "Missing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_assignment(self):
        assignment_id = services.create_assignment(
            self.course_id,
            "To Delete",
        )

        response = self.client.delete(
            f"/assignments/{assignment_id}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(
            f"/assignments/{assignment_id}"
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_assignment_returns_404(self):
        response = self.client.delete("/assignments/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Assignment not found.",
                }
            },
        )
