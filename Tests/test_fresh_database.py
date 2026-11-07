import shutil
import tempfile
import unittest
from pathlib import Path

import database
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
}

_TEST_DB_DIR = None
_ORIGINAL_DB_PATH = None
_FRESH_DB_EXISTED_BEFORE_INIT = None


def _clear_database():
    connection = database.get_connection()

    try:
        for table in (
            "resource_tags",
            "resources",
            "assignments",
            "study_sessions",
            "calendar_events",
            "tags",
            "courses",
        ):
            connection.execute(f"DELETE FROM {table}")

        connection.commit()

    finally:
        connection.close()


def setUpModule():
    global _TEST_DB_DIR
    global _ORIGINAL_DB_PATH
    global _FRESH_DB_EXISTED_BEFORE_INIT

    _ORIGINAL_DB_PATH = database.get_database_path()
    _TEST_DB_DIR = tempfile.mkdtemp(prefix="studyflow_fresh_tests_")
    fresh_db_path = Path(_TEST_DB_DIR) / "studyflow_fresh_test.db"

    _FRESH_DB_EXISTED_BEFORE_INIT = fresh_db_path.exists()

    database.configure_database(fresh_db_path)
    database.initialize_database()


def tearDownModule():
    global _TEST_DB_DIR
    global _ORIGINAL_DB_PATH
    global _FRESH_DB_EXISTED_BEFORE_INIT

    if _ORIGINAL_DB_PATH is not None:
        database.configure_database(_ORIGINAL_DB_PATH)

    if _TEST_DB_DIR is not None:
        shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)

    _TEST_DB_DIR = None
    _ORIGINAL_DB_PATH = None
    _FRESH_DB_EXISTED_BEFORE_INIT = None


class TestFreshDatabase(unittest.TestCase):

    def setUp(self):
        _clear_database()

    def test_database_path_points_to_fresh_temporary_file(self):
        self.assertFalse(_FRESH_DB_EXISTED_BEFORE_INIT)
        self.assertIsNotNone(_TEST_DB_DIR)

        database_path = Path(database.get_database_path())

        self.assertEqual(database_path.parent, Path(_TEST_DB_DIR))
        self.assertTrue(database_path.exists())
        self.assertNotEqual(
            database_path,
            database.DEFAULT_DATABASE_PATH,
        )

    def test_required_tables_are_created(self):
        connection = database.get_connection()

        try:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                """
            ).fetchall()

        finally:
            connection.close()

        table_names = {row["name"] for row in rows}

        self.assertEqual(table_names, _REQUIRED_TABLES)

    def test_fresh_database_tables_start_empty(self):
        connection = database.get_connection()

        try:
            for table in sorted(_REQUIRED_TABLES):
                count = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

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
