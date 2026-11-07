from database import get_connection
from models import (
    Course,
    Assignment,
    Resource,
    StudySession,
    CalendarEvent,
    Tag
)
from validators import (
    validate_date,
    validate_datetime,
    validate_datetime_order,
    validate_non_negative_integer,
    validate_optional_text,
    validate_required_text,
    validate_tag_name,
)
from constants import (
    DEFAULT_ASSIGNMENT_PRIORITY,
    DEFAULT_ASSIGNMENT_STATUS,
    DEFAULT_RESOURCE_STATUS,
)
_UNSET = object()


def _update_row(connection, table, record_id, values):
    """Update only explicitly supplied columns.

    Values equal to ``_UNSET`` are left unchanged. Returns True when a row
    matched the update.
    """

    columns = []
    parameters = []

    for column, value in values.items():
        if value is _UNSET:
            continue
        columns.append(f"{column} = ?")
        parameters.append(value)

    if not columns:
        return False

    parameters.append(record_id)

    cursor = connection.execute(
        f"UPDATE {table} SET {', '.join(columns)} WHERE id = ?",
        parameters,
    )

    connection.commit()
    return cursor.rowcount > 0


def create_course(
    name,
    instructor=None,
    credits=None,
    semester=None,
    color=None
):
    """Create a new course and return its ID."""
    name = validate_required_text(name, "Course name")
    instructor = validate_optional_text(
        instructor,
        "Instructor",
)
    credits = validate_non_negative_integer(
        credits,
        "Credits",
        allow_none=True,
)
    semester = validate_optional_text(
        semester,
        "Semester",
)
    color = validate_optional_text(
        color,
        "Color",
)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO courses (
                name,
                instructor,
                credits,
                semester,
                color
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                instructor,
                credits,
                semester,
                color
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_all_courses(active_only=False):
    """Return all courses from the database."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT *
            FROM courses
        """

        if active_only:
            query += """
                WHERE is_active = 1
            """

        query += """
            ORDER BY name
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        return [
            Course(
                id=row["id"],
                name=row["name"],
                instructor=row["instructor"],
                credits=row["credits"],
                semester=row["semester"],
                color=row["color"],
                is_active=bool(row["is_active"])
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_course_by_id(course_id):
    """Return a course by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM courses
            WHERE id = ?
            """,
            (course_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Course(
            id=row["id"],
            name=row["name"],
            instructor=row["instructor"],
            credits=row["credits"],
            semester=row["semester"],
            color=row["color"],
            is_active=bool(row["is_active"])
        )

    finally:
        connection.close()


def update_course(
    course_id,
    name=_UNSET,
    instructor=_UNSET,
    credits=_UNSET,
    semester=_UNSET,
    color=_UNSET,
    is_active=_UNSET
):
    """Update only explicitly supplied fields of an existing course."""
    if name is not _UNSET:
        name = validate_required_text(name, "Course name")

    if instructor is not _UNSET:
        instructor = validate_optional_text(
            instructor,
            "Instructor",
    )

    if credits is not _UNSET:
        credits = validate_non_negative_integer(
            credits,
            "Credits",
            allow_none=True,
    )

    if semester is not _UNSET:
        semester = validate_optional_text(
            semester,
            "Semester",
    )

    if color is not _UNSET:
        color = validate_optional_text(
            color,
            "Color",
    )
    connection = get_connection()

    try:
        values = {
            "name": name,
            "instructor": instructor,
            "credits": credits,
            "semester": semester,
            "color": color,
            "is_active": (
                _UNSET if is_active is _UNSET else int(is_active)
            ),
        }

        return _update_row(connection, "courses", course_id, values)

    finally:
        connection.close()


def set_course_active(course_id, is_active):
    """Archive or restore a course without removing related data.

    Setting ``is_active`` to False archives the course. Assignments,
    study sessions, resources, and calendar events stay linked to it.
    """

    return update_course(course_id, is_active=is_active)


def delete_course(course_id):
    """Delete a course and apply its related-data semantics.

    Assignments and study sessions are deleted together with the course.
    Resources and calendar events are kept but detached from it, matching
    the foreign-key actions defined in the database schema.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM courses
            WHERE id = ?
            """,
            (course_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# =========================
# ASSIGNMENT SERVICES
# =========================

def create_assignment(
    course_id,
    title,
    description=None,
    deadline=None,
    status=DEFAULT_ASSIGNMENT_STATUS,
    priority=DEFAULT_ASSIGNMENT_PRIORITY,
    progress=0,
):
    """Create a new assignment and return its ID."""
    title = validate_required_text(title, "Assignment title")

    description = validate_optional_text(
        description,
        "Description",
)
    deadline = validate_date(
        deadline,
        "Deadline",
        allow_none=True,
    )
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO assignments (
                course_id,
                title,
                description,
                deadline,
                status,
                priority,
                progress
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                title,
                description,
                deadline,
                status,
                priority,
                progress,
            ),
        )

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()

def get_all_assignments():
    """Return all assignments."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM assignments
            ORDER BY deadline IS NULL, deadline ASC
        """)

        rows = cursor.fetchall()

        return [
            Assignment(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                description=row["description"],
                deadline=row["deadline"],
                status=row["status"],
                priority=row["priority"],
                progress=row["progress"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_assignments_by_course(course_id):
    """Return all assignments for a specific course."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM assignments
            WHERE course_id = ?
            ORDER BY deadline IS NULL, deadline ASC
            """,
            (course_id,),
        )

        rows = cursor.fetchall()

        return [
            Assignment(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                description=row["description"],
                deadline=row["deadline"],
                status=row["status"],
                priority=row["priority"],
                progress=row["progress"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_assignment_by_id(assignment_id):
    """Return an assignment by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM assignments
            WHERE id = ?
            """,
            (assignment_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Assignment(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            description=row["description"],
            deadline=row["deadline"],
            status=row["status"],
            priority=row["priority"],
            progress=row["progress"],
        )

    finally:
        connection.close()


def update_assignment(
    assignment_id,
    course_id=_UNSET,
    title=_UNSET,
    description=_UNSET,
    deadline=_UNSET,
    status=_UNSET,
    priority=_UNSET,
    progress=_UNSET,
):
    """Update only explicitly supplied fields of an existing assignment."""
    if title is not _UNSET:
        title = validate_required_text(
            title,
            "Assignment title",
    )

    if description is not _UNSET:
        description = validate_optional_text(
            description,
            "Description",
    )
    if deadline is not _UNSET:
        deadline = validate_date(
            deadline,
            "Deadline",
            allow_none=True,
        )
    connection = get_connection()

    try:
        values = {
            "course_id": course_id,
            "title": title,
            "description": description,
            "deadline": deadline,
            "status": status,
            "priority": priority,
            "progress": progress,
        }

        return _update_row(
            connection,
            "assignments",
            assignment_id,
            values,
        )

    finally:
        connection.close()


def delete_assignment(assignment_id):
    """Delete an assignment by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM assignments
            WHERE id = ?
            """,
            (assignment_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

# =========================
# RESOURCE SERVICES
# =========================

def create_resource(
    title,
    resource_type,
    course_id=None,
    author=None,
    category=None,
    url=None,
    status=DEFAULT_RESOURCE_STATUS,
    notes=None,
):
    """Create a new resource and return its ID."""
    title = validate_required_text(title, "Resource title")

    url = validate_optional_text(
        url,
        "URL",
)

    notes = validate_optional_text(
        notes,
        "Notes",
)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO resources (
                course_id,
                title,
                resource_type,
                author,
                category,
                url,
                status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                title,
                resource_type,
                author,
                category,
                url,
                status,
                notes,
            ),
        )

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_resources():
    """Return all resources."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM resources
            ORDER BY title
        """)

        rows = cursor.fetchall()

        return [
            Resource(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                resource_type=row["resource_type"],
                author=row["author"],
                category=row["category"],
                url=row["url"],
                status=row["status"],
                notes=row["notes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_resources_by_course(course_id):
    """Return all resources for a specific course."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM resources
            WHERE course_id = ?
            ORDER BY title
            """,
            (course_id,),
        )

        rows = cursor.fetchall()

        return [
            Resource(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                resource_type=row["resource_type"],
                author=row["author"],
                category=row["category"],
                url=row["url"],
                status=row["status"],
                notes=row["notes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_resource_by_id(resource_id):
    """Return a resource by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM resources
            WHERE id = ?
            """,
            (resource_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Resource(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            resource_type=row["resource_type"],
            author=row["author"],
            category=row["category"],
            url=row["url"],
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
        )

    finally:
        connection.close()


def update_resource(
    resource_id,
    title=_UNSET,
    resource_type=_UNSET,
    course_id=_UNSET,
    author=_UNSET,
    category=_UNSET,
    url=_UNSET,
    status=_UNSET,
    notes=_UNSET,
):
    """Update only explicitly supplied fields of an existing resource."""
    if title is not _UNSET:
        title = validate_required_text(
            title,
            "Resource title",
    )

    if url is not _UNSET:
        url = validate_optional_text(
            url,
            "URL",
    )

    if notes is not _UNSET:
        notes = validate_optional_text(
            notes,
            "Notes",
    )
    connection = get_connection()

    try:
        values = {
            "course_id": course_id,
            "title": title,
            "resource_type": resource_type,
            "author": author,
            "category": category,
            "url": url,
            "status": status,
            "notes": notes,
        }

        return _update_row(
            connection,
            "resources",
            resource_id,
            values,
        )

    finally:
        connection.close()


def delete_resource(resource_id):
    """Delete a resource by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM resources
            WHERE id = ?
            """,
            (resource_id,),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()

# =========================
# STUDY SESSION SERVICES
# =========================

def create_study_session(
    course_id,
    study_date,
    duration_minutes,
    notes=None,
):
    """Create a new study session and return its ID."""
    study_date = validate_date(
        study_date,
        "Study date",
)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO study_sessions (
                course_id,
                study_date,
                duration_minutes,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                course_id,
                study_date,
                duration_minutes,
                notes,
            ),
        )

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_study_sessions():
    """Return all study sessions."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM study_sessions
            ORDER BY study_date DESC, id DESC
            """
        )

        rows = cursor.fetchall()

        return [
            StudySession(
                id=row["id"],
                course_id=row["course_id"],
                study_date=row["study_date"],
                duration_minutes=row["duration_minutes"],
                notes=row["notes"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_study_sessions_by_course(course_id):
    """Return all study sessions for a specific course."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM study_sessions
            WHERE course_id = ?
            ORDER BY study_date DESC, id DESC
            """,
            (course_id,),
        )

        rows = cursor.fetchall()

        return [
            StudySession(
                id=row["id"],
                course_id=row["course_id"],
                study_date=row["study_date"],
                duration_minutes=row["duration_minutes"],
                notes=row["notes"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_study_session_by_id(session_id):
    """Return a study session by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM study_sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return StudySession(
            id=row["id"],
            course_id=row["course_id"],
            study_date=row["study_date"],
            duration_minutes=row["duration_minutes"],
            notes=row["notes"],
        )

    finally:
        connection.close()


def update_study_session(
    session_id,
    course_id,
    study_date,
    duration_minutes,
    notes=None,
):
    """Update an existing study session."""
    study_date = validate_date(
        study_date,
        "Study date",
)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE study_sessions
            SET
                course_id = ?,
                study_date = ?,
                duration_minutes = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                course_id,
                study_date,
                duration_minutes,
                notes,
                session_id,
            ),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def delete_study_session(session_id):
    """Delete a study session by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM study_sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()

# =========================
# CALENDAR EVENT SERVICES
# =========================

def create_calendar_event(
    title,
    event_type,
    start_datetime,
    course_id=None,
    end_datetime=None,
    description=None,
):
    """Create a new calendar event and return its ID."""
    title = validate_required_text(
        title,
        "Calendar event title",
)

    description = validate_optional_text(
        description,
        "Description",
)
    start_datetime = validate_datetime(
        start_datetime,
        "Start datetime",
)

    end_datetime = validate_datetime(
        end_datetime,
        "End datetime",
        allow_none=True,
)
    validate_datetime_order(
        start_datetime,
        end_datetime,
)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO calendar_events (
                course_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                description,
            ),
        )

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_calendar_events():
    """Return all calendar events."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM calendar_events
            ORDER BY start_datetime ASC
            """
        )

        rows = cursor.fetchall()

        return [
            CalendarEvent(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                event_type=row["event_type"],
                start_datetime=row["start_datetime"],
                end_datetime=row["end_datetime"],
                description=row["description"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_calendar_events_by_course(course_id):
    """Return all calendar events for a specific course."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM calendar_events
            WHERE course_id = ?
            ORDER BY start_datetime ASC
            """,
            (course_id,),
        )

        rows = cursor.fetchall()

        return [
            CalendarEvent(
                id=row["id"],
                course_id=row["course_id"],
                title=row["title"],
                event_type=row["event_type"],
                start_datetime=row["start_datetime"],
                end_datetime=row["end_datetime"],
                description=row["description"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_calendar_event_by_id(event_id):
    """Return a calendar event by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM calendar_events
            WHERE id = ?
            """,
            (event_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return CalendarEvent(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            event_type=row["event_type"],
            start_datetime=row["start_datetime"],
            end_datetime=row["end_datetime"],
            description=row["description"],
        )

    finally:
        connection.close()


def update_calendar_event(
    event_id,
    title=_UNSET,
    event_type=_UNSET,
    start_datetime=_UNSET,
    course_id=_UNSET,
    end_datetime=_UNSET,
    description=_UNSET,
):
    """Update only explicitly supplied fields of an existing calendar event."""
    if title is not _UNSET:
        title = validate_required_text(
            title,
            "Calendar event title",
    )

    if description is not _UNSET:
        description = validate_optional_text(
            description,
            "Description",
    )
    if start_datetime is not _UNSET:
        start_datetime = validate_datetime(
            start_datetime,
            "Start datetime",
    )

    if end_datetime is not _UNSET:
        end_datetime = validate_datetime(
            end_datetime,
            "End datetime",
            allow_none=True,
    )
    connection = get_connection()

    try:
        values = {
            "course_id": course_id,
            "title": title,
            "event_type": event_type,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "description": description,
        }

        return _update_row(
            connection,
            "calendar_events",
            event_id,
            values,
        )

    finally:
        connection.close()


def delete_calendar_event(event_id):
    """Delete a calendar event by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM calendar_events
            WHERE id = ?
            """,
            (event_id,),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()

# =========================
# TAG SERVICES
# =========================

def create_tag(name):
    """Create a new tag and return its ID."""
    name = validate_tag_name(name)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO tags (name)
            VALUES (?)
            """,
            (name,),
        )

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_tags():
    """Return all tags."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM tags
            ORDER BY name
            """
        )

        rows = cursor.fetchall()

        return [
            Tag(
                id=row["id"],
                name=row["name"],
            )
            for row in rows
        ]

    finally:
        connection.close()


def get_tag_by_id(tag_id):
    """Return a tag by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM tags
            WHERE id = ?
            """,
            (tag_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Tag(
            id=row["id"],
            name=row["name"],
        )

    finally:
        connection.close()


def update_tag(tag_id, name):
    """Update a tag."""
    if name is not _UNSET:
        name = validate_tag_name(name)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE tags
            SET name = ?
            WHERE id = ?
            """,
            (name, tag_id),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def delete_tag(tag_id):
    """Delete a tag by its ID."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM tags
            WHERE id = ?
            """,
            (tag_id,),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


# =========================
# RESOURCE TAG SERVICES
# =========================

def add_tag_to_resource(resource_id, tag_id):
    """Assign a tag to a resource."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO resource_tags (
                resource_id,
                tag_id
            )
            VALUES (?, ?)
            ON CONFLICT (resource_id, tag_id) DO NOTHING
            """,
            (resource_id, tag_id),
        )

        connection.commit()

    finally:
        connection.close()


def remove_tag_from_resource(resource_id, tag_id):
    """Remove a tag from a resource."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM resource_tags
            WHERE resource_id = ?
            AND tag_id = ?
            """,
            (resource_id, tag_id),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_tags_for_resource(resource_id):
    """Return all tags assigned to a resource."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT tags.*
            FROM tags
            INNER JOIN resource_tags
                ON tags.id = resource_tags.tag_id
            WHERE resource_tags.resource_id = ?
            ORDER BY tags.name
            """,
            (resource_id,),
        )

        rows = cursor.fetchall()

        return [
            Tag(
                id=row["id"],
                name=row["name"],
            )
            for row in rows
        ]

    finally:
        connection.close()
