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


class TestCoursesApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)

    def test_list_courses(self):
        first_id = services.create_course(
            "Algorithms",
            instructor="Ada",
        )
        second_id = services.create_course(
            "Databases",
            credits=3,
        )

        response = self.client.get("/courses")

        self.assertEqual(response.status_code, 200)

        courses = response.json()
        self.assertEqual(
            [course["id"] for course in courses],
            [first_id, second_id],
        )
        self.assertEqual(courses[0]["name"], "Algorithms")
        self.assertTrue(courses[0]["is_active"])

        services.set_course_active(second_id, False)

        active_response = self.client.get(
            "/courses",
            params={"active_only": True},
        )

        self.assertEqual(active_response.status_code, 200)
        self.assertEqual(
            [course["id"] for course in active_response.json()],
            [first_id],
        )

    def test_get_existing_course(self):
        course_id = services.create_course(
            "Algorithms",
            instructor="Ada",
            credits=3,
            semester="Fall",
            color="#123456",
        )

        response = self.client.get(f"/courses/{course_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": course_id,
                "name": "Algorithms",
                "instructor": "Ada",
                "credits": 3,
                "semester": "Fall",
                "color": "#123456",
                "is_active": True,
            },
        )

    def test_get_missing_course_returns_404(self):
        response = self.client.get("/courses/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Course not found.",
                }
            },
        )

    def test_create_course(self):
        payload = {
            "name": "Operating Systems",
            "instructor": "Grace",
            "credits": 4,
            "semester": "Spring",
            "color": "#abcdef",
        }

        response = self.client.post("/courses", json=payload)

        self.assertEqual(response.status_code, 201)

        course = response.json()
        self.assertIsInstance(course["id"], int)
        self.assertEqual(
            course,
            {
                "id": course["id"],
                **payload,
                "is_active": True,
            },
        )

        get_response = self.client.get(
            f"/courses/{course['id']}"
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), course)

    def test_create_course_missing_name_returns_422(self):
        response = self.client.post(
            "/courses",
            json={"instructor": "Grace"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_course_with_blank_name_returns_400(self):
        response = self.client.post(
            "/courses",
            json={"name": "   "},
        )

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

    def test_partial_update_preserves_untouched_fields(self):
        course_id = services.create_course(
            "Algorithms",
            instructor="Ada",
            credits=3,
            semester="Fall",
            color="#123456",
        )

        response = self.client.patch(
            f"/courses/{course_id}",
            json={"name": "Advanced Algorithms"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": course_id,
                "name": "Advanced Algorithms",
                "instructor": "Ada",
                "credits": 3,
                "semester": "Fall",
                "color": "#123456",
                "is_active": True,
            },
        )

    def test_delete_course(self):
        course_id = services.create_course("To Delete")

        response = self.client.delete(f"/courses/{course_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(f"/courses/{course_id}")

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_course_returns_404(self):
        response = self.client.delete("/courses/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Course not found.",
                }
            },
        )
