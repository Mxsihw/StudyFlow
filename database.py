import os
import sqlite3
from pathlib import Path


DATABASE_NAME = "studyflow.db"
DEFAULT_DATABASE_PATH = Path(__file__).parent / DATABASE_NAME
DATABASE_PATH = Path(
    os.environ.get("STUDYFLOW_DB_PATH", str(DEFAULT_DATABASE_PATH))
)


def configure_database(database_path):
    """Configure the database path used by future connections."""
    global DATABASE_PATH
    DATABASE_PATH = Path(database_path)


def get_database_path():
    """Return the database path used by new connections."""
    return DATABASE_PATH


def get_connection():
    """Create and return a connection to the SQLite database."""
    connection = sqlite3.connect(get_database_path())

    try:
        connection.row_factory = sqlite3.Row

        # Enable foreign key support in SQLite.
        connection.execute("PRAGMA foreign_keys = ON")

    except Exception:
        connection.close()
        raise

    return connection


def initialize_database():
    """Create all StudyFlow database tables if they do not exist."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # --------------------
        # COURSES
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                instructor TEXT,
                credits INTEGER,
                semester TEXT,
                color TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        # --------------------
        # ASSIGNMENTS
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                status TEXT NOT NULL DEFAULT 'Not Started',
                priority TEXT NOT NULL DEFAULT 'Medium',
                progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),

                FOREIGN KEY (course_id)
                    REFERENCES courses(id)
                    ON DELETE CASCADE
            )
        """)

        # --------------------
        # RESOURCES
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                author TEXT,
                category TEXT,
                url TEXT,
                status TEXT NOT NULL DEFAULT 'Not Started',
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (course_id)
                    REFERENCES courses(id)
                    ON DELETE SET NULL
            )
        """)

        # --------------------
        # STUDY SESSIONS
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                study_date TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL
                    CHECK(duration_minutes > 0),
                notes TEXT,

                FOREIGN KEY (course_id)
                    REFERENCES courses(id)
                    ON DELETE CASCADE
            )
        """)

        # --------------------
        # CALENDAR EVENTS
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT,
                description TEXT,

                FOREIGN KEY (course_id)
                    REFERENCES courses(id)
                    ON DELETE SET NULL
            )
        """)

        # --------------------
        # TAGS
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # --------------------
        # RESOURCE TAGS
        # Many-to-Many relationship
        # --------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_tags (
                resource_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,

                PRIMARY KEY (resource_id, tag_id),

                FOREIGN KEY (resource_id)
                    REFERENCES resources(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (tag_id)
                    REFERENCES tags(id)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("StudyFlow database initialized successfully!")
