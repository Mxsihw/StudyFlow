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


class TestCalendarEventsApi(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)
        self.course_id = services.create_course("Algorithms")

    def test_list_calendar_events(self):
        later_id = services.create_calendar_event(
            "Later",
            "Exam",
            "2026-06-01 10:00",
        )
        sooner_id = services.create_calendar_event(
            "Sooner",
            "Lecture",
            "2026-05-01 10:00",
        )

        response = self.client.get("/calendar-events")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [event["id"] for event in response.json()],
            [sooner_id, later_id],
        )

    def test_list_calendar_events_filters_by_course(self):
        other_course_id = services.create_course("Databases")
        first_id = services.create_calendar_event(
            "Algorithms exam",
            "Exam",
            "2026-05-01 10:00",
            course_id=self.course_id,
        )
        services.create_calendar_event(
            "Databases exam",
            "Exam",
            "2026-05-02 10:00",
            course_id=other_course_id,
        )
        services.create_calendar_event(
            "Personal event",
            "Other",
            "2026-05-03 10:00",
        )

        response = self.client.get(
            "/calendar-events",
            params={"course_id": self.course_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [event["id"] for event in response.json()],
            [first_id],
        )
        self.assertEqual(
            response.json()[0]["course_id"],
            self.course_id,
        )

    def test_get_existing_calendar_event(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
            course_id=self.course_id,
            end_datetime="2026-05-01 12:00",
            description="Room 101",
        )

        response = self.client.get(
            f"/calendar-events/{event_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": event_id,
                "course_id": self.course_id,
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 10:00",
                "end_datetime": "2026-05-01 12:00",
                "description": "Room 101",
            },
        )

    def test_get_missing_calendar_event_returns_404(self):
        response = self.client.get("/calendar-events/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Calendar event not found.",
                }
            },
        )

    def test_create_calendar_event(self):
        payload = {
            "title": "Midterm",
            "event_type": "Exam",
            "start_datetime": "2026-05-01 10:00",
            "course_id": self.course_id,
            "end_datetime": "2026-05-01 12:00",
            "description": "Room 101",
        }

        response = self.client.post(
            "/calendar-events",
            json=payload,
        )

        self.assertEqual(response.status_code, 201)

        event = response.json()
        self.assertIsInstance(event["id"], int)
        self.assertEqual(
            event,
            {"id": event["id"], **payload},
        )

        get_response = self.client.get(
            f"/calendar-events/{event['id']}"
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), event)

    def test_create_calendar_event_without_end_or_course(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Study block",
                "event_type": "Study",
                "start_datetime": "2026-05-01 10:00",
            },
        )

        self.assertEqual(response.status_code, 201)

        event = response.json()
        self.assertIsNone(event["course_id"])
        self.assertIsNone(event["end_datetime"])
        self.assertIsNone(event["description"])

    def test_create_calendar_event_normalizes_jalali_datetime(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "1405-01-01 10:30",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["start_datetime"],
            "2026-03-21 10:30",
        )

    def test_create_calendar_event_missing_fields_returns_422(self):
        response = self.client.post(
            "/calendar-events",
            json={"title": "Midterm"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "request_validation_error",
        )

    def test_create_calendar_event_with_blank_title_returns_400(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "   ",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 10:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": (
                        "Calendar event title cannot be empty."
                    ),
                }
            },
        )

    def test_create_calendar_event_with_invalid_datetime_returns_400(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "not-a-datetime",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_create_calendar_event_with_end_before_start_returns_400(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 12:00",
                "end_datetime": "2026-05-01 10:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "validation_error",
                    "message": (
                        "End datetime must be after start datetime."
                    ),
                }
            },
        )

    def test_create_calendar_event_with_equal_start_end_returns_400(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 10:00",
                "end_datetime": "2026-05-01 10:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_create_calendar_event_for_missing_course_returns_409(self):
        response = self.client.post(
            "/calendar-events",
            json={
                "title": "Midterm",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 10:00",
                "course_id": 999999,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "conflict",
        )

    def test_partial_update_preserves_untouched_fields(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
            course_id=self.course_id,
            end_datetime="2026-05-01 12:00",
            description="Room 101",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={"title": "Final"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": event_id,
                "course_id": self.course_id,
                "title": "Final",
                "event_type": "Exam",
                "start_datetime": "2026-05-01 10:00",
                "end_datetime": "2026-05-01 12:00",
                "description": "Room 101",
            },
        )

    def test_partial_update_start_after_existing_end_returns_400(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
            end_datetime="2026-05-01 12:00",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={"start_datetime": "2026-05-01 13:00"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_partial_update_end_before_existing_start_returns_400(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
            end_datetime="2026-05-01 12:00",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={"end_datetime": "2026-05-01 09:00"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_partial_update_can_clear_end_datetime(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
            end_datetime="2026-05-01 12:00",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={"end_datetime": None},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["end_datetime"])

    def test_empty_update_returns_current_event(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], event_id)
        self.assertEqual(response.json()["title"], "Midterm")

    def test_update_missing_calendar_event_returns_404(self):
        response = self.client.patch(
            "/calendar-events/999999",
            json={"title": "Missing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"],
            "not_found",
        )

    def test_update_calendar_event_with_invalid_datetime_returns_400(self):
        event_id = services.create_calendar_event(
            "Midterm",
            "Exam",
            "2026-05-01 10:00",
        )

        response = self.client.patch(
            f"/calendar-events/{event_id}",
            json={"start_datetime": "not-a-datetime"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"],
            "validation_error",
        )

    def test_delete_calendar_event(self):
        event_id = services.create_calendar_event(
            "To Delete",
            "Other",
            "2026-05-01 10:00",
        )

        response = self.client.delete(
            f"/calendar-events/{event_id}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        get_response = self.client.get(
            f"/calendar-events/{event_id}"
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(
            get_response.json()["error"]["code"],
            "not_found",
        )

    def test_delete_missing_calendar_event_returns_404(self):
        response = self.client.delete("/calendar-events/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "not_found",
                    "message": "Calendar event not found.",
                }
            },
        )
