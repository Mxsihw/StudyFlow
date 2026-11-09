# StudyFlow

StudyFlow is a Python study-management backend built on PostgreSQL. It provides a
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
├── database.py               # PostgreSQL DSN, connections, and schema setup
├── models.py                 # Dataclasses for stored records
├── services.py               # Service-layer database operations
├── validators.py             # Input and date/datetime validation
├── requirements.txt          # Third-party dependencies
├── .env.example              # Local PostgreSQL configuration template
├── README.md
└── Tests/
    ├── __init__.py
    ├── db_test_utils.py      # Isolated PostgreSQL schemas for tests
    ├── test_fresh_database.py
    ├── test_services.py
    └── test_validators.py
```

## Requirements

- Python 3.10 or newer
- A running PostgreSQL server with a database for StudyFlow
- `jdatetime`, `psycopg[binary]`, and `python-dotenv` (installed from
  `requirements.txt`)

## Setup

1. Obtain the project and open a terminal in the project root directory.

2. Create the PostgreSQL database used by StudyFlow. The default configuration
   expects a database named `studyflow`:

   ```bash
   createdb -U postgres studyflow
   ```

3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment.

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

5. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Create your local environment file from the template and replace
   `YOUR_PASSWORD` with your PostgreSQL password:

   ```bash
   cp .env.example .env
   ```

   The `.env` file is ignored by Git and must not be committed.

## Initialize and run

The entry point initializes the PostgreSQL schema and creates any missing
tables:

```bash
python database.py
```

StudyFlow loads `STUDYFLOW_DB_URL` from the local `.env` file. Without that
setting, it falls back to `postgresql://postgres@localhost:5432/studyflow`.
To use a different server or database, update `.env` or set the
`STUDYFLOW_DB_URL` environment variable before running Python:

```powershell
$env:STUDYFLOW_DB_URL = "postgresql://user:password@host:5432/studyflow"
```

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

The tests create and initialize isolated PostgreSQL schemas, so they do not
modify existing StudyFlow tables. They require a reachable PostgreSQL database.
The test DSN is read from `STUDYFLOW_TEST_DB_URL`, then `STUDYFLOW_DB_URL`, and
finally the default DSN above:

```powershell
$env:STUDYFLOW_TEST_DB_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/studyflow_test"
python -m unittest discover -v
```
