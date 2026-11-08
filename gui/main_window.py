from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.pages.dashboard import DashboardPage
from gui.pages.courses import CoursesPage
from gui.pages.assignments import AssignmentsPage
from gui.pages.resources import ResourcesPage
from gui.pages.study_sessions import StudySessionsPage
from gui.pages.calendar_page import CalendarPage
from gui.pages.settings import SettingsPage

from gui.i18n import (
    apply_layout_direction,
    apply_translations,
    get_language,
    install_translator,
    is_rtl,
    set_language,
    tr,
)

from gui.theme import apply_theme


# ============================================================
# NAVIGATION DEFINITION
# ============================================================

NAV_ITEMS = (
    ("dashboard", "⌂", "Dashboard"),
    ("courses", "▣", "Courses"),
    ("assignments", "✎", "Assignments"),
    ("resources", "▤", "Resources"),
    ("study_sessions", "◷", "Study Sessions"),
    ("calendar", "▦", "Calendar"),
)

SETTINGS_ITEM = ("settings", "⚙", "Settings")

CONTENT_PAGE_ATTRS = (
    "dashboard_page",
    "courses_page",
    "assignments_page",
    "resources_page",
    "study_sessions_page",
    "calendar_page",
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sidebar_expanded = True
        self.nav_buttons = {}
        self.nav_icons = {}
        self.nav_labels = {}

        self.current_page_name = "dashboard"
        self.settings_page = None

        self.apply_global_direction()

        self.setWindowTitle("StudyFlow")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self.setup_ui()
        self.connect_signals()

        install_translator(QApplication.instance())
        self.retranslate_ui()

    # ========================================================
    # DIRECTION / LANGUAGE
    # ========================================================

    def apply_global_direction(self):
        direction = (
            Qt.LayoutDirection.RightToLeft
            if is_rtl()
            else Qt.LayoutDirection.LeftToRight
        )

        application = QApplication.instance()

        if application is not None:
            application.setLayoutDirection(direction)

        self.setLayoutDirection(direction)

        if hasattr(self, "main_layout"):
            self.main_layout.setDirection(
                QBoxLayout.Direction.RightToLeft
                if is_rtl()
                else QBoxLayout.Direction.LeftToRight
            )

            self.main_layout.invalidate()

    # ========================================================
    # MAIN UI
    # ========================================================

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        self.main_layout = main_layout

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(self.sidebar)

        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        # -- Logo --------------------------------------------

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.logo_label = QLabel("SF")
        self.logo_label.setObjectName("appLogo")

        self.app_name_label = QLabel("StudyFlow")
        self.app_name_label.setObjectName("appName")

        top_layout.addWidget(self.logo_label)
        top_layout.addWidget(self.app_name_label)
        top_layout.addStretch()

        sidebar_layout.addLayout(top_layout)
        sidebar_layout.addSpacing(18)

        # -- Navigation --------------------------------------

        for name, icon, label in NAV_ITEMS:
            self.create_nav_button(name, icon, label)

        sidebar_layout.addStretch()

        self.create_nav_button(*SETTINGS_ITEM)

        sidebar_layout.addSpacing(8)

        # -- Collapse button (always at the bottom) ----------

        self.collapse_button = QPushButton("☰")

        self.collapse_button.setObjectName("collapseButton")
        self.collapse_button.setProperty("i18n_skip", True)
        self.collapse_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.collapse_button.setFixedHeight(42)
        self.collapse_button.clicked.connect(self.toggle_sidebar)

        sidebar_layout.addWidget(self.collapse_button)

        # ----------------------------------------------------
        # PAGES
        # ----------------------------------------------------

        self.pages = QStackedWidget()

        self.create_content_pages()

        self.settings_page = SettingsPage()

        self.pages.addWidget(self.settings_page)

        # ----------------------------------------------------
        # ADD TO MAIN LAYOUT
        # ----------------------------------------------------

        main_layout.addWidget(self.sidebar)

        main_layout.addWidget(self.pages, stretch=1)

        self.apply_global_direction()

        self.set_current_page("dashboard")

    # ========================================================
    # CREATE PAGES
    # ========================================================

    def create_content_pages(self):
        self.dashboard_page = DashboardPage()
        self.courses_page = CoursesPage()
        self.assignments_page = AssignmentsPage()
        self.resources_page = ResourcesPage()
        self.study_sessions_page = StudySessionsPage()
        self.calendar_page = CalendarPage()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.courses_page)
        self.pages.addWidget(self.assignments_page)
        self.pages.addWidget(self.resources_page)
        self.pages.addWidget(self.study_sessions_page)
        self.pages.addWidget(self.calendar_page)

    def page_map(self):
        return {
            "dashboard": self.dashboard_page,
            "courses": self.courses_page,
            "assignments": self.assignments_page,
            "resources": self.resources_page,
            "study_sessions": self.study_sessions_page,
            "calendar": self.calendar_page,
            "settings": self.settings_page,
        }

    def rebuild_content_pages(self):
        """Recreate every page except Settings to refresh localized text."""

        selected_name = self.current_page_name

        if self.settings_page is not None:
            self.pages.removeWidget(self.settings_page)

        for attr in CONTENT_PAGE_ATTRS:
            page = getattr(self, attr, None)

            if page is None:
                continue

            self.pages.removeWidget(page)
            page.setParent(None)
            page.deleteLater()
            setattr(self, attr, None)

        self.create_content_pages()

        if self.settings_page is not None:
            self.pages.addWidget(self.settings_page)

        page = self.page_map().get(selected_name)

        if page is not None:
            self.pages.setCurrentWidget(page)
        else:
            self.current_page_name = "dashboard"
            self.pages.setCurrentWidget(self.dashboard_page)

        self.update_nav_texts()

    # ========================================================
    # CREATE NAV BUTTON
    # ========================================================

    def create_nav_button(
        self,
        name,
        icon,
        label,
    ):
        button = QPushButton()

        button.setObjectName("sidebarButton")
        button.setProperty("i18n_skip", True)
        button.setCheckable(True)
        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        button.setMinimumHeight(44)

        button.clicked.connect(
            lambda _checked=False,
            page_name=name:
            self.set_current_page(page_name)
        )

        self.nav_buttons[name] = button
        self.nav_icons[name] = icon
        self.nav_labels[name] = label

        # Add button before the stretch.
        self.sidebar.layout().addWidget(button)

        self.update_nav_button(name)

    def update_nav_button(self, name):
        button = self.nav_buttons.get(name)

        if button is None:
            return

        icon = self.nav_icons[name]
        label = tr(self.nav_labels[name])

        if self.sidebar_expanded:
            button.setText(f"{icon}  {label}")
            button.setToolTip("")
            button.setStyleSheet(
                "text-align: right;"
                if is_rtl()
                else "text-align: left;"
            )

        else:
            button.setText(icon)
            button.setToolTip(label)
            button.setStyleSheet(
                """
                text-align: center;
                padding-left: 0px;
                padding-right: 0px;
                """
            )

    def update_nav_texts(self):
        for name in self.nav_buttons:
            self.update_nav_button(name)

    # ========================================================
    # PAGE NAVIGATION
    # ========================================================

    def set_current_page(self, name):
        page = self.page_map().get(name)

        if page is None:
            return

        self.pages.setCurrentWidget(page)
        self.current_page_name = name

        for button_name, button in self.nav_buttons.items():
            button.setChecked(button_name == name)

        self.refresh_current_page(name)

    # ========================================================
    # REFRESH PAGES
    # ========================================================

    def refresh_current_page(self, page_name):
        page = self.page_map().get(page_name)

        if page is None:
            return

        if hasattr(page, "refresh_data"):
            try:
                page.refresh_data()
            except Exception:
                # Errors are handled by the page itself.
                pass

    # ========================================================
    # COLLAPSE SIDEBAR
    # ========================================================

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded

        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(230)
            self.app_name_label.show()

        else:
            self.sidebar.setFixedWidth(76)
            self.app_name_label.hide()

        self.collapse_button.setText("☰")

        self.update_nav_texts()

    # ========================================================
    # SETTINGS SIGNALS
    # ========================================================

    def connect_signals(self):
        self.settings_page.settings_changed.connect(
            self.on_settings_changed
        )

    # ========================================================
    # APPLY SETTINGS
    # ========================================================

    def on_settings_changed(self, settings):
        application = QApplication.instance()

        if application is None:
            return

        new_language = settings.get(
            "language",
            get_language(),
        )

        language_changed = new_language != get_language()

        if language_changed:
            set_language(new_language)

        self.apply_global_direction()

        apply_theme(
            application,
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

        if language_changed:
            self.rebuild_content_pages()

        self.retranslate_ui()

    # ========================================================
    # RETRANSLATE
    # ========================================================

    def retranslate_ui(self):
        self.update_nav_texts()

        apply_layout_direction(self)

        apply_translations(self)
