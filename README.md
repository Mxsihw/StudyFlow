# StudyFlow

StudyFlow is a Python study-management backend built on SQLite. It provides a
validated service layer for organizing courses, assignments, learning resources,
study sessions, calendar events, and tags. The current project exposes its
functionality through Python modules; there is no graphical interface yet.

## Features

- Course management, including archiving/restoring through the `is_active` flag
  and deletion with defined related-data behavior.
- Assignment management with deadlines, status, priority, progress, and deadline
  sorting.
- Resource management with optional course association and tags.
- Study session tracking with dates, durations, and notes.
- Calendar event management with optional course association.
- Tag management with whitespace normalization, empty-name rejection, duplicate
  prevention, and idempotent assignment to resources.
- Input validation for required/optional text, non-negative integers, and
  Gregorian or Jalali dates and datetimes.
- Automatic database schema initialization and foreign-key enforcement.

### Course archive and delete behavior

- Archiving a course (setting `is_active` to `False`) keeps all related records.
- Deleting a course removes its assignments and study sessions.
- Deleting a course keeps its resources and calendar events, but clears their
  `course_id` so they are no longer linked to the deleted course.

## Project structure

```text
StudyFlow/
├── constants.py              # Default values and status/priority options
├── database.py               # Database path, connections, and schema setup
├── models.py                 # Dataclasses for stored records
├── services.py               # Service-layer database operations
├── validators.py             # Input and date/datetime validation
├── requirements.txt          # Third-party dependencies
├── README.md
├── studyflow.db              # Local SQLite database (ignored by git)
└── Tests/
    ├── __init__.py
    ├── test_fresh_database.py
    ├── test_services.py
    └── test_validators.py
```

## Requirements

- Python 3.9 or newer
- `jdatetime` (installed from `requirements.txt`)
- SQLite support, which is included with the Python standard library

## Setup

1. Obtain the project and open a terminal in the project root directory.

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment.

   Windows (PowerShell):

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   Windows (Command Prompt):

   ```bat
   .venv\Scripts\activate.bat
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

4. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

## Initialize and run

The current entry point initializes the SQLite database and creates any missing
tables:

```bash
python database.py
```

By default, the database file is `studyflow.db` in the project root. To use a
different location, set the `STUDYFLOW_DB_PATH` environment variable before
running Python.

The service layer can then be used directly from Python:

```python
from database import initialize_database
from services import create_course, get_all_courses

initialize_database()
course_id = create_course("Database Systems")
print(get_all_courses())
```

## Running the tests

From the project root, run the complete test suite with:

```bash
python -m unittest discover -v
```

The tests create and initialize their own temporary databases, so they do not
depend on or modify the local `studyflow.db` file.
