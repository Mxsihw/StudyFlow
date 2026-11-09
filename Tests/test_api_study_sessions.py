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


class TestStudySessionsApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)
        self.course_id = services.create_course("Algorithms")

    def test_list_study_sessions(self):
        january_id = services.create_study_session(
            self.course_id,
            "2026-01-15",
            30,
        )
        march_id = services.create_study_session(
            self.course_id,
            "2026-03-01",
            45,
        )
        february_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )

        response = self.client.get("/study-sessions")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [session["id"] for session in response.json()],
            [march_id, february_id, january_id],
        )

    def test_list_study_sessions_filters_by_course(self):
        other_course_id = services.create_course("Databases")
        first_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )
        services.create_study_session(
            other_course_id,
            "2026-02-02",
            30,
        )

        response = self.client.get(
            "/study-sessions",
            params={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [session["id"] for session in response.json()],
            [first_id],
        )
        self.assertEqual(
            response.json()[0]["course_id"],
            self.course_id,
        )

    def test_get_existing_study_session(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
            notes="Chapter 1",
        )

        response = self.client.get(
            f"/study-sessions/{session_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": session_id,
                "course_id": self.course_id,
                "study_date": "2026-02-01",
                "duration_minutes": 60,
                "notes": "Chapter 1",
            },
        )

    def test_get_missing_study_session_returns_404(self):
        response = self.client.get("/study-sessions/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Study session not found.",
                }
            },
        )

    def test_create_study_session(self):
        payload = {
            "course_id": self.course_id,
            "study_date": "2026-02-01",
            "duration_minutes": 60,
            "notes": "Chapter 1",
        }

        response = self.client.post(
            "/study-sessions",
            json=payload,
        )

        self.assertEqual(response.status_code, 201)

        session = response.json()
        self.assertIsInstance(session["id"], int)
        self.assertEqual(
            session,
            {"id": session["id"], **payload},
        )

        get_response = self.client.get(
            f"/study-sessions/{session['id']}"
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), session)

    def test_create_study_session_normalizes_jalali_date(self):
        response = self.client.post(
            "/study-sessions",
            json={
                "course_id": self.course_id,
                "study_date": "1405-01-01",
                "duration_minutes": 30,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["study_date"],
            "2026-03-21",
        )

    def test_create_study_session_missing_fields_returns_422(self):
        response = self.client.post(
            "/study-sessions",
            json={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_study_session_with_invalid_date_returns_400(self):
        response = self.client.post(
            "/study-sessions",
            json={
                "course_id": self.course_id,
                "study_date": "not-a-date",
                "duration_minutes": 30,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": (
                        "Study date must be in YYYY-MM-DD format."
                    ),
                }
            },
        )

    def test_create_study_session_for_missing_course_returns_409(self):
        response = self.client.post(
            "/study-sessions",
            json={
                "course_id": 999999,
                "study_date": "2026-02-01",
                "duration_minutes": 30,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_create_study_session_with_non_positive_duration_returns_409(
        self,
    ):
        response = self.client.post(
            "/study-sessions",
            json={
                "course_id": self.course_id,
                "study_date": "2026-02-01",
                "duration_minutes": 0,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_partial_update_preserves_untouched_fields(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
            notes="Chapter 1",
        )

        response = self.client.patch(
            f"/study-sessions/{session_id}",
            json={"duration_minutes": 90},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": session_id,
                "course_id": self.course_id,
                "study_date": "2026-02-01",
                "duration_minutes": 90,
                "notes": "Chapter 1",
            },
        )

    def test_partial_update_changes_date(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )

        response = self.client.patch(
            f"/study-sessions/{session_id}",
            json={"study_date": "2026-02-15"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["study_date"],
            "2026-02-15",
        )

    def test_empty_update_returns_current_session(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )

        response = self.client.patch(
            f"/study-sessions/{session_id}",
            json={},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], session_id)
        self.assertEqual(
            response.json()["duration_minutes"],
            60,
        )

    def test_update_missing_study_session_returns_404(self):
        response = self.client.patch(
            "/study-sessions/999999",
            json={"duration_minutes": 30},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_update_study_session_with_invalid_date_returns_400(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )

        response = self.client.patch(
            f"/study-sessions/{session_id}",
            json={"study_date": "not-a-date"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_delete_study_session(self):
        session_id = services.create_study_session(
            self.course_id,
            "2026-02-01",
            60,
        )

        response = self.client.delete(
            f"/study-sessions/{session_id}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(
            f"/study-sessions/{session_id}"
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_study_session_returns_404(self):
        response = self.client.delete("/study-sessions/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Study session not found.",
                }
            },
        )
