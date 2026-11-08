import json
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

import database

from gui.main_window import MainWindow
from gui.i18n import is_rtl, set_language
from gui.theme import apply_theme


# ============================================================
# SETTINGS
# ============================================================

SETTINGS_FILE = Path("user_settings.json")

DEFAULT_SETTINGS = {
    "appearance": "Dark",
    "color_scheme": "Purple + Pink",
    "language": "English",
}


def load_settings():
    """
    Load saved application settings.
    """

    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            saved_settings = json.load(file)

        settings = DEFAULT_SETTINGS.copy()

        settings.update(
            saved_settings
        )

        return settings

    except Exception:
        return DEFAULT_SETTINGS.copy()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Initialize the StudyFlow database.
    """

    try:
        database.initialize_database()

    except AttributeError:
        # Compatibility fallback in case the project's
        # database module uses another initialization name.
        pass


# ============================================================
# APPLICATION
# ============================================================

def main():
    """
    Start StudyFlow.
    """

    # --------------------------------------------------------
    # CREATE APPLICATION
    # --------------------------------------------------------

    app = QApplication(sys.argv)

    app.setApplicationName(
        "StudyFlow"
    )

    app.setOrganizationName(
        "StudyFlow"
    )

    # --------------------------------------------------------
    # INITIALIZE DATABASE
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # LOAD SETTINGS
    # --------------------------------------------------------

    settings = load_settings()

    # --------------------------------------------------------
    # APPLY LANGUAGE
    # --------------------------------------------------------

    set_language(
        settings.get(
            "language",
            "English",
        )
    )

    # --------------------------------------------------------
    # APPLY THEME
    # --------------------------------------------------------

    apply_theme(
        app,
        appearance=settings.get(
            "appearance",
            "Dark",
        ),
        color_scheme=settings.get(
            "color_scheme",
            "Purple + Pink",
        ),
        rtl=is_rtl(),
    )

    # --------------------------------------------------------
    # CREATE MAIN WINDOW
    # --------------------------------------------------------

    window = MainWindow()

    window.show()

    # --------------------------------------------------------
    # START EVENT LOOP
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()