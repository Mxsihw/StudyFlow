import unittest

import database
from Tests.db_test_utils import create_test_schema, drop_test_schema
from services import (
    create_course,
    get_course_by_id,
    create_assignment,
    get_assignment_by_id,
    create_resource,
    get_resource_by_id,
    create_study_session,
    get_study_session_by_id,
    create_calendar_event,
    get_calendar_event_by_id,
    create_tag,
    add_tag_to_resource,
    get_tags_for_resource,
)

_REQUIRED_TABLES = {
    "courses",
    "assignments",
    "resources",
    "study_sessions",
    "calendar_events",
    "tags",
    "resource_tags",
    "users",
    "user_preferences",
}

_TEST_DB_SCHEMA = None
_ORIGINAL_DB_URL = None


def _clear_database():
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


class TestFreshDatabase(unittest.TestCase):

    def setUp(self):
        _clear_database()

    def test_tests_use_isolated_schema(self):
        self.assertIsNotNone(_TEST_DB_SCHEMA)

        connection = database.get_connection()

        try:
            row = connection.execute(
                "SELECT current_schema() AS schema"
            ).fetchone()

        finally:
            connection.close()

        self.assertEqual(row["schema"], _TEST_DB_SCHEMA)
        self.assertNotEqual(
            database.get_database_url(),
            database.DEFAULT_DATABASE_URL,
        )

    def test_required_tables_are_created(self):
        connection = database.get_connection()

        try:
            rows = connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                """
            ).fetchall()

        finally:
            connection.close()

        table_names = {row["table_name"] for row in rows}

        self.assertEqual(table_names, _REQUIRED_TABLES)

    def test_fresh_database_tables_start_empty(self):
        connection = database.get_connection()

        try:
            for table in sorted(_REQUIRED_TABLES):
                count = connection.execute(
                    f"SELECT COUNT(*) AS count FROM {table}"
                ).fetchone()["count"]

                self.assertEqual(count, 0, table)

        finally:
            connection.close()

    def test_initialize_database_can_run_again(self):
        database.initialize_database()

        course_id = create_course("Fresh Course")

        self.assertIsNotNone(get_course_by_id(course_id))

    def test_basic_services_work_on_fresh_database(self):
        course_id = create_course(
            name="Fresh Course",
            instructor="Fresh Instructor",
        )
        assignment_id = create_assignment(
            course_id,
            "Fresh Assignment",
        )
        session_id = create_study_session(
            course_id,
            "2026-11-04",
            60,
        )
        resource_id = create_resource(
            "Fresh Resource",
            "Book",
            course_id=course_id,
        )
        event_id = create_calendar_event(
            "Fresh Event",
            "Exam",
            "2026-12-20 09:00",
            course_id=course_id,
        )

        self.assertEqual(
            get_course_by_id(course_id).name,
            "Fresh Course",
        )
        self.assertEqual(
            get_assignment_by_id(assignment_id).course_id,
            course_id,
        )
        self.assertEqual(
            get_study_session_by_id(session_id).course_id,
            course_id,
        )
        self.assertEqual(
            get_resource_by_id(resource_id).course_id,
            course_id,
        )
        self.assertEqual(
            get_calendar_event_by_id(event_id).course_id,
            course_id,
        )

    def test_tag_services_work_on_fresh_database(self):
        resource_id = create_resource(
            "Fresh Resource",
            "Book",
        )

        tag_id = create_tag("  Python  ")

        add_tag_to_resource(resource_id, tag_id)
        add_tag_to_resource(resource_id, tag_id)

        tags = get_tags_for_resource(resource_id)

        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].name, "Python")


if __name__ == "__main__":
    unittest.main()
