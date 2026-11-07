import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database
from database import initialize_database
from services import (
    create_course,
    get_all_courses,
    get_course_by_id,
    update_course,
    delete_course,
    set_course_active,

    create_assignment,
    get_all_assignments,
    get_assignments_by_course,
    get_assignment_by_id,
    update_assignment,
    delete_assignment,

    create_resource,
    get_all_resources,
    get_resources_by_course,
    get_resource_by_id,
    update_resource,
    delete_resource,

    create_study_session,
    get_all_study_sessions,
    get_study_sessions_by_course,
    get_study_session_by_id,
    update_study_session,
    delete_study_session,

    create_calendar_event,
    get_all_calendar_events,
    get_calendar_events_by_course,
    get_calendar_event_by_id,
    update_calendar_event,
    delete_calendar_event,

    create_tag,
    get_all_tags,
    get_tag_by_id,
    update_tag,
    delete_tag,

    add_tag_to_resource,
    remove_tag_from_resource,
    get_tags_for_resource,
)
from validators import ValidationError

_TEST_DB_DIR = None


def setUpModule():
    global _TEST_DB_DIR

    _TEST_DB_DIR = tempfile.mkdtemp(prefix="studyflow_tests_")
    database.configure_database(Path(_TEST_DB_DIR) / "studyflow_test.db")
    initialize_database()


def tearDownModule():
    global _TEST_DB_DIR

    if _TEST_DB_DIR is not None:
        shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
        _TEST_DB_DIR = None


def reset_database():
    """Delete all rows so each test starts from a clean database."""

    connection = database.get_connection()

    try:
        connection.execute("DELETE FROM resource_tags")
        connection.execute("DELETE FROM resources")
        connection.execute("DELETE FROM assignments")
        connection.execute("DELETE FROM study_sessions")
        connection.execute("DELETE FROM calendar_events")
        connection.execute("DELETE FROM tags")
        connection.execute("DELETE FROM courses")
        connection.commit()

    finally:
        connection.close()


class TestDatabaseIsolation(unittest.TestCase):

    def test_tests_use_temporary_database(self):
        self.assertIsNotNone(_TEST_DB_DIR)
        self.assertEqual(
            Path(database.get_database_path()).parent,
            Path(_TEST_DB_DIR),
        )
        self.assertNotEqual(
            database.get_database_path(),
            database.DEFAULT_DATABASE_PATH,
        )

    def test_foreign_keys_are_enabled(self):
        connection = database.get_connection()

        try:
            enabled = connection.execute(
                "PRAGMA foreign_keys"
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertEqual(enabled, 1)


class TestCourseServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def create_related_records(self, course_id):
        return (
            create_assignment(course_id, "Linked Assignment"),
            create_study_session(course_id, "2026-11-04", 60),
            create_resource(
                "Linked Resource",
                "Book",
                course_id=course_id,
            ),
            create_calendar_event(
                "Linked Event",
                "Exam",
                "2026-12-20 09:00",
                course_id=course_id,
            ),
        )

    def test_create_course(self):
        course_id = create_course(
            name="Database",
            instructor="Test Instructor",
            credits=3,
            semester="Fall 2026",
            color="#3498db",
        )

        self.assertIsNotNone(course_id)

    def test_get_all_courses(self):
        create_course("Operating Systems")
        create_course("Database")

        courses = get_all_courses()

        self.assertEqual(len(courses), 2)

    def test_get_course_by_id(self):
        course_id = create_course(
            name="Computer Networks"
        )

        course = get_course_by_id(course_id)

        self.assertIsNotNone(course)
        self.assertEqual(course.name, "Computer Networks")

    def test_get_nonexistent_course(self):
        course = get_course_by_id(999999)

        self.assertIsNone(course)

    def test_update_course(self):
        course_id = create_course(
            name="Old Name"
        )

        updated = update_course(
            course_id=course_id,
            name="New Name",
            instructor="New Instructor",
            credits=3,
            semester="Fall 2026",
            color="#ff0000",
            is_active=True,
        )

        self.assertTrue(updated)

        course = get_course_by_id(course_id)

        self.assertEqual(course.name, "New Name")
        self.assertEqual(course.instructor, "New Instructor")

    def test_update_course_preserves_untouched_fields(self):
        course_id = create_course(
            name="Original Name",
            instructor="Original Instructor",
            credits=4,
            semester="Spring 2026",
            color="#123456",
        )

        self.assertTrue(set_course_active(course_id, False))

        updated = update_course(course_id, name="Renamed Course")

        self.assertTrue(updated)

        course = get_course_by_id(course_id)

        self.assertEqual(course.name, "Renamed Course")
        self.assertEqual(course.instructor, "Original Instructor")
        self.assertEqual(course.credits, 4)
        self.assertEqual(course.semester, "Spring 2026")
        self.assertEqual(course.color, "#123456")
        self.assertFalse(course.is_active)

    def test_set_course_active_only_changes_active_flag(self):
        course_id = create_course(
            name="Archived Course",
            instructor="Instructor",
            credits=2,
            semester="Fall 2026",
            color="#abcdef",
        )

        self.assertTrue(set_course_active(course_id, False))

        course = get_course_by_id(course_id)

        self.assertFalse(course.is_active)
        self.assertEqual(course.name, "Archived Course")
        self.assertEqual(course.instructor, "Instructor")
        self.assertEqual(course.credits, 2)
        self.assertEqual(course.semester, "Fall 2026")
        self.assertEqual(course.color, "#abcdef")

        self.assertTrue(set_course_active(course_id, True))

        course = get_course_by_id(course_id)

        self.assertTrue(course.is_active)
        self.assertEqual(course.name, "Archived Course")

    def test_update_nonexistent_course(self):
        updated = update_course(
            course_id=999999,
            name="Does Not Exist"
        )

        self.assertFalse(updated)

    def test_delete_course(self):
        course_id = create_course(
            name="Course To Delete"
        )

        deleted = delete_course(course_id)

        self.assertTrue(deleted)

        course = get_course_by_id(course_id)

        self.assertIsNone(course)

    def test_delete_nonexistent_course(self):
        deleted = delete_course(999999)

        self.assertFalse(deleted)

    def test_archive_course_preserves_related_records(self):
        course_id = create_course("Archived Course")

        (
            assignment_id,
            session_id,
            resource_id,
            event_id,
        ) = self.create_related_records(course_id)

        self.assertTrue(set_course_active(course_id, False))

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

    def test_delete_course_cascades_assignments_and_study_sessions(self):
        course_id = create_course("Course To Delete")

        (
            assignment_id,
            session_id,
            _,
            _,
        ) = self.create_related_records(course_id)

        self.assertTrue(delete_course(course_id))

        self.assertIsNone(get_assignment_by_id(assignment_id))
        self.assertIsNone(get_study_session_by_id(session_id))

    def test_delete_course_detaches_resources_and_calendar_events(self):
        course_id = create_course("Course To Delete")

        (
            _,
            _,
            resource_id,
            event_id,
        ) = self.create_related_records(course_id)

        self.assertTrue(delete_course(course_id))

        resource = get_resource_by_id(resource_id)
        event = get_calendar_event_by_id(event_id)

        self.assertIsNotNone(resource)
        self.assertIsNotNone(event)
        self.assertIsNone(resource.course_id)
        self.assertIsNone(event.course_id)

    def test_delete_course_leaves_no_orphaned_related_records(self):
        course_id = create_course("Course To Delete")

        self.create_related_records(course_id)

        self.assertTrue(delete_course(course_id))

        connection = database.get_connection()

        try:
            counts = {
                "assignments": connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM assignments
                    WHERE course_id = ?
                    """,
                    (course_id,),
                ).fetchone()[0],
                "study_sessions": connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM study_sessions
                    WHERE course_id = ?
                    """,
                    (course_id,),
                ).fetchone()[0],
                "resources": connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM resources
                    WHERE course_id = ?
                    """,
                    (course_id,),
                ).fetchone()[0],
                "calendar_events": connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM calendar_events
                    WHERE course_id = ?
                    """,
                    (course_id,),
                ).fetchone()[0],
            }

        finally:
            connection.close()

        self.assertEqual(
            counts,
            {
                "assignments": 0,
                "study_sessions": 0,
                "resources": 0,
                "calendar_events": 0,
            },
        )

    def test_active_only_courses(self):
        active_id = create_course(
            name="Active Course"
        )

        inactive_id = create_course(
            name="Inactive Course"
        )

        update_course(
            course_id=inactive_id,
            name="Inactive Course",
            is_active=False,
        )

        courses = get_all_courses(active_only=True)

        course_ids = [course.id for course in courses]

        self.assertIn(active_id, course_ids)
        self.assertNotIn(inactive_id, course_ids)
class TestAssignmentServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def create_test_course(self):
        return create_course(
            name="Database",
            instructor="Test Instructor",
            credits=3,
            semester="Fall 2026",
        )

    def test_create_assignment(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id=course_id,
            title="Database Homework 1",
            description="Design ER Diagram",
            deadline="2026-11-10",
            priority="High",
        )

        self.assertIsNotNone(assignment_id)

    def test_get_all_assignments(self):
        course_id = self.create_test_course()

        create_assignment(course_id, "Homework 1")
        create_assignment(course_id, "Homework 2")

        assignments = get_all_assignments()

        self.assertEqual(len(assignments), 2)

    def test_assignments_are_sorted_by_deadline_with_none_last(self):
        course_id = self.create_test_course()

        create_assignment(
            course_id,
            "No Deadline",
        )

        create_assignment(
            course_id,
            "Later",
            deadline="2026-12-20",
        )

        create_assignment(
            course_id,
            "Sooner",
            deadline="2026-11-10",
        )

        assignments = get_all_assignments()

        titles = [assignment.title for assignment in assignments]

        self.assertEqual(
            titles,
            [
                "Sooner",
                "Later",
                "No Deadline",
            ],
        )

    def test_get_assignment_by_id(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "Operating Systems Assignment",
        )

        assignment = get_assignment_by_id(assignment_id)

        self.assertIsNotNone(assignment)
        self.assertEqual(
            assignment.title,
            "Operating Systems Assignment",
        )

    def test_get_nonexistent_assignment(self):
        assignment = get_assignment_by_id(999999)

        self.assertIsNone(assignment)

    def test_get_assignments_by_course(self):
        course_1 = create_course("Database")
        course_2 = create_course("Computer Networks")

        create_assignment(course_1, "Database Homework")
        create_assignment(course_1, "SQL Practice")

        create_assignment(course_2, "Network Homework")

        assignments = get_assignments_by_course(course_1)

        self.assertEqual(len(assignments), 2)

        for assignment in assignments:
            self.assertEqual(assignment.course_id, course_1)

    def test_course_assignments_are_sorted_by_deadline_with_none_last(self):
        course_id = self.create_test_course()

        create_assignment(
            course_id,
            "No Deadline",
        )

        create_assignment(
            course_id,
            "Later",
            deadline="2026-12-20",
        )

        create_assignment(
            course_id,
            "Sooner",
            deadline="2026-11-10",
        )

        assignments = get_assignments_by_course(course_id)

        titles = [assignment.title for assignment in assignments]

        self.assertEqual(
            titles,
            [
                "Sooner",
                "Later",
                "No Deadline",
            ],
        )

    def test_update_assignment(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "Old Assignment",
        )

        updated = update_assignment(
            assignment_id=assignment_id,
            course_id=course_id,
            title="Updated Assignment",
            description="Updated description",
            deadline="2026-12-01",
            status="In Progress",
            priority="High",
            progress=50,
        )

        self.assertTrue(updated)

        assignment = get_assignment_by_id(assignment_id)

        self.assertEqual(
            assignment.title,
            "Updated Assignment",
        )

        self.assertEqual(
            assignment.status,
            "In Progress",
        )

        self.assertEqual(
            assignment.progress,
            50,
        )

    def test_update_assignment_preserves_untouched_fields(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "Original Assignment",
            description="Original description",
            deadline="2026-12-01",
            status="In Progress",
            priority="High",
            progress=40,
        )

        updated = update_assignment(
            assignment_id,
            status="Completed",
        )

        self.assertTrue(updated)

        assignment = get_assignment_by_id(assignment_id)

        self.assertEqual(assignment.course_id, course_id)
        self.assertEqual(assignment.title, "Original Assignment")
        self.assertEqual(assignment.description, "Original description")
        self.assertEqual(assignment.deadline, "2026-12-01")
        self.assertEqual(assignment.status, "Completed")
        self.assertEqual(assignment.priority, "High")
        self.assertEqual(assignment.progress, 40)

    def test_update_nonexistent_assignment(self):
        course_id = self.create_test_course()

        updated = update_assignment(
            assignment_id=999999,
            course_id=course_id,
            title="Does Not Exist",
        )

        self.assertFalse(updated)

    def test_delete_assignment(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "Assignment To Delete",
        )

        deleted = delete_assignment(assignment_id)

        self.assertTrue(deleted)

        assignment = get_assignment_by_id(assignment_id)

        self.assertIsNone(assignment)

    def test_delete_nonexistent_assignment(self):
        deleted = delete_assignment(999999)

        self.assertFalse(deleted)

    def test_assignment_course_must_exist(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_assignment(
                course_id=999999,
                title="Invalid Assignment",
            )

    def test_progress_can_be_zero(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "New Assignment",
            progress=0,
        )

        assignment = get_assignment_by_id(assignment_id)

        self.assertEqual(assignment.progress, 0)

    def test_progress_can_be_100(self):
        course_id = self.create_test_course()

        assignment_id = create_assignment(
            course_id,
            "Completed Assignment",
            status="Completed",
            progress=100,
        )

        assignment = get_assignment_by_id(assignment_id)

        self.assertEqual(assignment.progress, 100)
class TestResourceServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def create_test_course(self):
        return create_course(
            name="Database",
            instructor="Test Instructor",
            credits=3,
            semester="Fall 2026",
        )

    def test_create_resource(self):
        course_id = self.create_test_course()

        resource_id = create_resource(
            title="Database Book",
            resource_type="Book",
            course_id=course_id,
            author="Test Author",
            category="Reference",
            url="https://example.com",
            notes="Important chapters",
        )

        self.assertIsNotNone(resource_id)

    def test_create_resource_without_course(self):
        resource_id = create_resource(
            title="General Python Guide",
            resource_type="Article",
        )

        resource = get_resource_by_id(resource_id)

        self.assertIsNone(resource.course_id)

    def test_get_all_resources(self):
        create_resource("Book A", "Book")
        create_resource("Article B", "Article")

        resources = get_all_resources()

        self.assertEqual(len(resources), 2)

    def test_get_resource_by_id(self):
        resource_id = create_resource(
            title="Python Documentation",
            resource_type="Website",
        )

        resource = get_resource_by_id(resource_id)

        self.assertIsNotNone(resource)
        self.assertEqual(resource.title, "Python Documentation")

    def test_get_nonexistent_resource(self):
        resource = get_resource_by_id(999999)

        self.assertIsNone(resource)

    def test_get_resources_by_course(self):
        course_1 = create_course("Database")
        course_2 = create_course("Computer Networks")

        create_resource(
            "Database Book",
            "Book",
            course_id=course_1,
        )

        create_resource(
            "SQL Notes",
            "Notes",
            course_id=course_1,
        )

        create_resource(
            "Network Book",
            "Book",
            course_id=course_2,
        )

        resources = get_resources_by_course(course_1)

        self.assertEqual(len(resources), 2)

        for resource in resources:
            self.assertEqual(resource.course_id, course_1)

    def test_update_resource(self):
        course_id = self.create_test_course()

        resource_id = create_resource(
            title="Old Book",
            resource_type="Book",
            course_id=course_id,
        )

        updated = update_resource(
            resource_id=resource_id,
            title="Updated Book",
            resource_type="PDF",
            course_id=course_id,
            author="New Author",
            category="Important",
            url="https://example.com/new",
            status="In Progress",
            notes="Updated notes",
        )

        self.assertTrue(updated)

        resource = get_resource_by_id(resource_id)

        self.assertEqual(resource.title, "Updated Book")
        self.assertEqual(resource.resource_type, "PDF")
        self.assertEqual(resource.status, "In Progress")

    def test_update_resource_preserves_untouched_fields(self):
        course_id = self.create_test_course()

        resource_id = create_resource(
            title="Original Resource",
            resource_type="Book",
            course_id=course_id,
            author="Original Author",
            category="Reference",
            url="https://example.com/original",
            status="In Progress",
            notes="Original notes",
        )

        updated = update_resource(
            resource_id,
            title="Renamed Resource",
        )

        self.assertTrue(updated)

        resource = get_resource_by_id(resource_id)

        self.assertEqual(resource.title, "Renamed Resource")
        self.assertEqual(resource.resource_type, "Book")
        self.assertEqual(resource.course_id, course_id)
        self.assertEqual(resource.author, "Original Author")
        self.assertEqual(resource.category, "Reference")
        self.assertEqual(resource.url, "https://example.com/original")
        self.assertEqual(resource.status, "In Progress")
        self.assertEqual(resource.notes, "Original notes")

    def test_update_nonexistent_resource(self):
        updated = update_resource(
            resource_id=999999,
            title="Does Not Exist",
            resource_type="Book",
        )

        self.assertFalse(updated)

    def test_delete_resource(self):
        resource_id = create_resource(
            title="Resource To Delete",
            resource_type="Article",
        )

        deleted = delete_resource(resource_id)

        self.assertTrue(deleted)

        resource = get_resource_by_id(resource_id)

        self.assertIsNone(resource)

    def test_delete_nonexistent_resource(self):
        deleted = delete_resource(999999)

        self.assertFalse(deleted)

    def test_resource_course_must_exist(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_resource(
                title="Invalid Resource",
                resource_type="Book",
                course_id=999999,
            )

    def test_resource_created_at_exists(self):
        resource_id = create_resource(
            title="Timestamp Test",
            resource_type="Notes",
        )

        resource = get_resource_by_id(resource_id)

        self.assertIsNotNone(resource.created_at)
class TestStudySessionServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def create_test_course(self):
        return create_course(
            name="Operating Systems",
            instructor="Test Instructor",
            credits=3,
            semester="Fall 2026",
        )

    def test_create_study_session(self):
        course_id = self.create_test_course()

        session_id = create_study_session(
            course_id=course_id,
            study_date="2026-11-04",
            duration_minutes=90,
            notes="Process Scheduling",
        )

        self.assertIsNotNone(session_id)

    def test_get_all_study_sessions(self):
        course_id = self.create_test_course()

        create_study_session(
            course_id,
            "2026-11-03",
            60,
        )

        create_study_session(
            course_id,
            "2026-11-04",
            90,
        )

        sessions = get_all_study_sessions()

        self.assertEqual(len(sessions), 2)

    def test_get_study_session_by_id(self):
        course_id = self.create_test_course()

        session_id = create_study_session(
            course_id,
            "2026-11-04",
            120,
            "Memory Management",
        )

        session = get_study_session_by_id(session_id)

        self.assertIsNotNone(session)
        self.assertEqual(session.duration_minutes, 120)
        self.assertEqual(session.notes, "Memory Management")

    def test_get_nonexistent_study_session(self):
        session = get_study_session_by_id(999999)

        self.assertIsNone(session)

    def test_get_study_sessions_by_course(self):
        course_1 = create_course("Operating Systems")
        course_2 = create_course("Database")

        create_study_session(course_1, "2026-11-03", 60)
        create_study_session(course_1, "2026-11-04", 90)
        create_study_session(course_2, "2026-11-04", 120)

        sessions = get_study_sessions_by_course(course_1)

        self.assertEqual(len(sessions), 2)

        for session in sessions:
            self.assertEqual(session.course_id, course_1)

    def test_update_study_session(self):
        course_id = self.create_test_course()

        session_id = create_study_session(
            course_id,
            "2026-11-03",
            60,
            "Old Notes",
        )

        updated = update_study_session(
            session_id=session_id,
            course_id=course_id,
            study_date="2026-11-04",
            duration_minutes=120,
            notes="Updated Notes",
        )

        self.assertTrue(updated)

        session = get_study_session_by_id(session_id)

        self.assertEqual(session.study_date, "2026-11-04")
        self.assertEqual(session.duration_minutes, 120)
        self.assertEqual(session.notes, "Updated Notes")

    def test_update_nonexistent_study_session(self):
        course_id = self.create_test_course()

        updated = update_study_session(
            session_id=999999,
            course_id=course_id,
            study_date="2026-11-04",
            duration_minutes=60,
        )

        self.assertFalse(updated)

    def test_delete_study_session(self):
        course_id = self.create_test_course()

        session_id = create_study_session(
            course_id,
            "2026-11-04",
            90,
        )

        deleted = delete_study_session(session_id)

        self.assertTrue(deleted)

        session = get_study_session_by_id(session_id)

        self.assertIsNone(session)

    def test_delete_nonexistent_study_session(self):
        deleted = delete_study_session(999999)

        self.assertFalse(deleted)

    def test_study_session_course_must_exist(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_study_session(
                course_id=999999,
                study_date="2026-11-04",
                duration_minutes=60,
            )

    def test_duration_must_be_positive(self):
        course_id = self.create_test_course()

        with self.assertRaises(sqlite3.IntegrityError):
            create_study_session(
                course_id=course_id,
                study_date="2026-11-04",
                duration_minutes=0,
            )

    def test_negative_duration_is_rejected(self):
        course_id = self.create_test_course()

        with self.assertRaises(sqlite3.IntegrityError):
            create_study_session(
                course_id=course_id,
                study_date="2026-11-04",
                duration_minutes=-30,
            )
class TestCalendarEventServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def create_test_course(self):
        return create_course(
            name="Database",
            instructor="Test Instructor",
            credits=3,
            semester="Fall 2026",
        )

    def test_create_calendar_event(self):
        course_id = self.create_test_course()

        event_id = create_calendar_event(
            title="Database Exam",
            event_type="Exam",
            start_datetime="2026-12-20 09:00",
            end_datetime="2026-12-20 11:00",
            course_id=course_id,
            description="Final exam",
        )

        self.assertIsNotNone(event_id)

    def test_create_event_without_course(self):
        event_id = create_calendar_event(
            title="Study Planning",
            event_type="Personal",
            start_datetime="2026-11-10 10:00",
        )

        event = get_calendar_event_by_id(event_id)

        self.assertIsNone(event.course_id)

    def test_get_all_calendar_events(self):
        create_calendar_event(
            "Event 2",
            "Exam",
            "2026-12-20 09:00",
        )

        create_calendar_event(
            "Event 1",
            "Class",
            "2026-11-10 08:00",
        )

        events = get_all_calendar_events()

        self.assertEqual(len(events), 2)

        # باید بر اساس تاریخ مرتب شده باشند
        self.assertEqual(events[0].title, "Event 1")

    def test_get_calendar_event_by_id(self):
        event_id = create_calendar_event(
            title="Operating Systems Exam",
            event_type="Exam",
            start_datetime="2026-12-01 09:00",
        )

        event = get_calendar_event_by_id(event_id)

        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Operating Systems Exam")
        self.assertEqual(event.event_type, "Exam")

    def test_get_nonexistent_calendar_event(self):
        event = get_calendar_event_by_id(999999)

        self.assertIsNone(event)

    def test_get_calendar_events_by_course(self):
        course_1 = create_course("Database")
        course_2 = create_course("Computer Networks")

        create_calendar_event(
            "Database Exam",
            "Exam",
            "2026-12-20 09:00",
            course_id=course_1,
        )

        create_calendar_event(
            "Database Class",
            "Class",
            "2026-11-10 08:00",
            course_id=course_1,
        )

        create_calendar_event(
            "Network Exam",
            "Exam",
            "2026-12-15 09:00",
            course_id=course_2,
        )

        events = get_calendar_events_by_course(course_1)

        self.assertEqual(len(events), 2)

        for event in events:
            self.assertEqual(event.course_id, course_1)

    def test_update_calendar_event(self):
        course_id = self.create_test_course()

        event_id = create_calendar_event(
            title="Old Exam",
            event_type="Exam",
            start_datetime="2026-11-20 09:00",
            course_id=course_id,
        )

        updated = update_calendar_event(
            event_id=event_id,
            title="Updated Exam",
            event_type="Final Exam",
            start_datetime="2026-12-20 10:00",
            end_datetime="2026-12-20 12:00",
            course_id=course_id,
            description="Updated description",
        )

        self.assertTrue(updated)

        event = get_calendar_event_by_id(event_id)

        self.assertEqual(event.title, "Updated Exam")
        self.assertEqual(event.event_type, "Final Exam")
        self.assertEqual(
            event.start_datetime,
            "2026-12-20 10:00",
        )

    def test_update_calendar_event_preserves_untouched_fields(self):
        course_id = self.create_test_course()

        event_id = create_calendar_event(
            title="Original Event",
            event_type="Exam",
            start_datetime="2026-12-20 09:00",
            course_id=course_id,
            end_datetime="2026-12-20 11:00",
            description="Original description",
        )

        updated = update_calendar_event(
            event_id,
            title="Renamed Event",
        )

        self.assertTrue(updated)

        event = get_calendar_event_by_id(event_id)

        self.assertEqual(event.title, "Renamed Event")
        self.assertEqual(event.event_type, "Exam")
        self.assertEqual(event.start_datetime, "2026-12-20 09:00")
        self.assertEqual(event.course_id, course_id)
        self.assertEqual(event.end_datetime, "2026-12-20 11:00")
        self.assertEqual(event.description, "Original description")

    def test_update_nonexistent_calendar_event(self):
        updated = update_calendar_event(
            event_id=999999,
            title="Does Not Exist",
            event_type="Exam",
            start_datetime="2026-12-20 09:00",
        )

        self.assertFalse(updated)

    def test_delete_calendar_event(self):
        event_id = create_calendar_event(
            title="Event To Delete",
            event_type="Personal",
            start_datetime="2026-11-10 10:00",
        )

        deleted = delete_calendar_event(event_id)

        self.assertTrue(deleted)

        event = get_calendar_event_by_id(event_id)

        self.assertIsNone(event)

    def test_delete_nonexistent_calendar_event(self):
        deleted = delete_calendar_event(999999)

        self.assertFalse(deleted)

    def test_calendar_event_course_must_exist(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_calendar_event(
                title="Invalid Event",
                event_type="Exam",
                start_datetime="2026-12-20 09:00",
                course_id=999999,
            )

    def test_events_are_sorted_by_start_datetime(self):
        create_calendar_event(
            "Late Event",
            "Exam",
            "2026-12-30 10:00",
        )

        create_calendar_event(
            "Early Event",
            "Class",
            "2026-11-01 08:00",
        )

        create_calendar_event(
            "Middle Event",
            "Deadline",
            "2026-11-15 12:00",
        )

        events = get_all_calendar_events()

        titles = [event.title for event in events]

        self.assertEqual(
            titles,
            ["Early Event", "Middle Event", "Late Event"],
        )
class TestTagServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def test_create_tag(self):
        tag_id = create_tag("Important")

        self.assertIsNotNone(tag_id)

    def test_create_tag_trims_surrounding_whitespace(self):
        tag_id = create_tag("  Python  ")

        tag = get_tag_by_id(tag_id)

        self.assertEqual(tag.name, "Python")

    def test_create_tag_rejects_whitespace_only_name(self):
        with self.assertRaises(ValidationError):
            create_tag("   ")

    def test_update_tag_trims_surrounding_whitespace(self):
        tag_id = create_tag("Old Tag")

        updated = update_tag(tag_id, "  Updated Tag  ")

        self.assertTrue(updated)

        tag = get_tag_by_id(tag_id)

        self.assertEqual(tag.name, "Updated Tag")

    def test_get_all_tags(self):
        create_tag("Python")
        create_tag("Database")

        tags = get_all_tags()

        self.assertEqual(len(tags), 2)

        tag_names = [tag.name for tag in tags]

        self.assertIn("Python", tag_names)
        self.assertIn("Database", tag_names)

    def test_get_tag_by_id(self):
        tag_id = create_tag("Exam")

        tag = get_tag_by_id(tag_id)

        self.assertIsNotNone(tag)
        self.assertEqual(tag.name, "Exam")

    def test_get_nonexistent_tag(self):
        tag = get_tag_by_id(999999)

        self.assertIsNone(tag)

    def test_update_tag(self):
        tag_id = create_tag("Old Tag")

        updated = update_tag(
            tag_id,
            "Updated Tag",
        )

        self.assertTrue(updated)

        tag = get_tag_by_id(tag_id)

        self.assertEqual(tag.name, "Updated Tag")

    def test_update_nonexistent_tag(self):
        updated = update_tag(
            999999,
            "Does Not Exist",
        )

        self.assertFalse(updated)

    def test_delete_tag(self):
        tag_id = create_tag("Tag To Delete")

        deleted = delete_tag(tag_id)

        self.assertTrue(deleted)

        tag = get_tag_by_id(tag_id)

        self.assertIsNone(tag)

    def test_delete_nonexistent_tag(self):
        deleted = delete_tag(999999)

        self.assertFalse(deleted)

    def test_duplicate_tag_is_rejected(self):
        create_tag("Python")

        with self.assertRaises(sqlite3.IntegrityError):
            create_tag("Python")

    def test_duplicate_tag_with_whitespace_is_rejected(self):
        create_tag("Python")

        with self.assertRaises(sqlite3.IntegrityError):
            create_tag("  Python  ")

        tags = get_all_tags()

        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].name, "Python")


class TestResourceTagServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def setUp(self):
        reset_database()

    def test_add_tag_to_resource(self):
        resource_id = create_resource(
            "Python Book",
            "Book",
        )

        tag_id = create_tag("Python")

        add_tag_to_resource(
            resource_id,
            tag_id,
        )

        tags = get_tags_for_resource(resource_id)

        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].name, "Python")

    def test_add_multiple_tags_to_resource(self):
        resource_id = create_resource(
            "Database Book",
            "Book",
        )

        tag_1 = create_tag("Database")
        tag_2 = create_tag("Important")

        add_tag_to_resource(resource_id, tag_1)
        add_tag_to_resource(resource_id, tag_2)

        tags = get_tags_for_resource(resource_id)

        self.assertEqual(len(tags), 2)

    def test_remove_tag_from_resource(self):
        resource_id = create_resource(
            "Network Notes",
            "Notes",
        )

        tag_id = create_tag("Networks")

        add_tag_to_resource(resource_id, tag_id)

        removed = remove_tag_from_resource(
            resource_id,
            tag_id,
        )

        self.assertTrue(removed)

        tags = get_tags_for_resource(resource_id)

        self.assertEqual(len(tags), 0)

    def test_remove_nonexistent_tag_from_resource(self):
        resource_id = create_resource(
            "Python Guide",
            "Article",
        )

        tag_id = create_tag("Python")

        removed = remove_tag_from_resource(
            resource_id,
            tag_id,
        )

        self.assertFalse(removed)

    def test_duplicate_resource_tag_is_idempotent(self):
        resource_id = create_resource(
            "Test Resource",
            "Book",
        )

        tag_id = create_tag("Test")

        add_tag_to_resource(resource_id, tag_id)
        add_tag_to_resource(resource_id, tag_id)

        tags = get_tags_for_resource(resource_id)

        self.assertEqual(len(tags), 1)

    def test_duplicate_assignment_creates_single_relationship(self):
        resource_id = create_resource(
            "Test Resource",
            "Book",
        )

        tag_id = create_tag("Test")

        add_tag_to_resource(resource_id, tag_id)
        add_tag_to_resource(resource_id, tag_id)

        connection = database.get_connection()

        try:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM resource_tags
                WHERE resource_id = ?
                AND tag_id = ?
                """,
                (resource_id, tag_id),
            ).fetchone()

        finally:
            connection.close()

        self.assertEqual(row[0], 1)

    def test_same_tag_can_be_assigned_to_different_resources(self):
        tag_id = create_tag("Python")

        resource_1 = create_resource("Python Book", "Book")
        resource_2 = create_resource("Python Guide", "Article")

        add_tag_to_resource(resource_1, tag_id)
        add_tag_to_resource(resource_2, tag_id)

        self.assertEqual(len(get_tags_for_resource(resource_1)), 1)
        self.assertEqual(len(get_tags_for_resource(resource_2)), 1)

    def test_resource_must_exist_for_tag(self):
        tag_id = create_tag("Test")

        with self.assertRaises(sqlite3.IntegrityError):
            add_tag_to_resource(
                999999,
                tag_id,
            )

    def test_tag_must_exist_for_resource(self):
        resource_id = create_resource(
            "Test Resource",
            "Book",
        )

        with self.assertRaises(sqlite3.IntegrityError):
            add_tag_to_resource(
                resource_id,
                999999,
            )

    def test_deleting_resource_removes_tag_relationships(self):
        resource_id = create_resource(
            "Test Resource",
            "Book",
        )

        tag_id = create_tag("Test")

        add_tag_to_resource(resource_id, tag_id)

        self.assertTrue(delete_resource(resource_id))

        self.assertEqual(get_tags_for_resource(resource_id), [])

        connection = database.get_connection()

        try:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM resource_tags
                WHERE resource_id = ?
                """,
                (resource_id,),
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertEqual(count, 0)

    def test_deleting_tag_removes_resource_relationships(self):
        resource_id = create_resource(
            "Test Resource",
            "Book",
        )

        tag_id = create_tag("Test")

        add_tag_to_resource(resource_id, tag_id)

        self.assertTrue(delete_tag(tag_id))

        self.assertEqual(get_tags_for_resource(resource_id), [])

        connection = database.get_connection()

        try:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM resource_tags
                WHERE tag_id = ?
                """,
                (tag_id,),
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertEqual(count, 0)

if __name__ == "__main__":
    unittest.main()
