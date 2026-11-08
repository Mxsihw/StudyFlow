from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import (
    add_combo_item,
    format_date,
    format_duration,
    localize_digits,
    tr,
    trf,
)

from gui.widgets import (
    DangerButton,
    EmptyState,
    PageHeader,
    PrimaryButton,
    SecondaryButton,
    confirm_delete,
    show_error,
)

from services import (
    create_study_session,
    delete_study_session,
    get_all_courses,
    get_all_study_sessions,
    update_study_session,
)


class StudySessionDialog(QDialog):
    def __init__(self, study_session=None, parent=None):
        super().__init__(parent)

        self.study_session = study_session
        self.courses = []

        self.setWindowTitle(
            "Add Study Session"
            if study_session is None
            else "Edit Study Session"
        )

        self.setMinimumWidth(500)

        self.setup_ui()
        self.load_courses()

        if self.study_session is not None:
            self.load_session_data()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # ----------------------------------------------------
        # COURSE
        # ----------------------------------------------------

        self.course_input = QComboBox()

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        self.date_input = QLineEdit()

        self.date_input.setPlaceholderText(
            "YYYY-MM-DD or Jalali date"
        )

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        self.duration_input = QSpinBox()

        self.duration_input.setRange(
            1,
            1440,
        )

        self.duration_input.setValue(
            60
        )

        self.duration_input.setSuffix(
            tr(" minutes")
        )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        self.notes_input = QTextEdit()

        self.notes_input.setPlaceholderText(
            "What did you study? (Optional)"
        )

        self.notes_input.setFixedHeight(
            110
        )

        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        form.addRow(
            "Course *",
            self.course_input,
        )

        form.addRow(
            "Study Date *",
            self.date_input,
        )

        form.addRow(
            "Duration *",
            self.duration_input,
        )

        form.addRow(
            "Notes",
            self.notes_input,
        )

        layout.addLayout(
            form
        )

        layout.addSpacing(
            10
        )

        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        buttons = QDialogButtonBox()

        buttons.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        buttons.addButton(
            "Save",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        buttons.rejected.connect(
            self.reject
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        layout.addWidget(
            buttons
        )

    # ========================================================
    # LOAD COURSES
    # ========================================================

    def load_courses(self):
        try:
            self.courses = get_all_courses()

        except Exception as error:
            show_error(
                self,
                "Unable to load courses",
                str(error),
            )

            return

        self.course_input.clear()

        for course in self.courses:
            if course.is_active:
                self.course_input.addItem(
                    course.name,
                    course.id,
                )

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_session_data(self):
        session = self.study_session

        self.date_input.setText(
            session.study_date
        )

        self.duration_input.setValue(
            session.duration_minutes
        )

        self.notes_input.setPlainText(
            session.notes or ""
        )

        for index in range(
            self.course_input.count()
        ):
            if (
                self.course_input.itemData(index)
                == session.course_id
            ):
                self.course_input.setCurrentIndex(
                    index
                )
                break

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_and_accept(self):
        if self.course_input.currentData() is None:
            show_error(
                self,
                "Course required",
                "Please select a course.",
            )

            return

        if not self.date_input.text().strip():
            show_error(
                self,
                "Date required",
                "Please enter the study date.",
            )

            return

        if self.duration_input.value() <= 0:
            show_error(
                self,
                "Invalid duration",
                "Duration must be greater than zero.",
            )

            return

        self.accept()

    # ========================================================
    # DATA
    # ========================================================

    def get_data(self):
        notes = (
            self.notes_input
            .toPlainText()
            .strip()
        )

        return {
            "course_id":
                self.course_input.currentData(),

            "study_date":
                self.date_input.text().strip(),

            "duration_minutes":
                self.duration_input.value(),

            "notes":
                notes or None,
        }


class StudySessionCard(QFrame):
    def __init__(
        self,
        study_session,
        course_name,
        on_edit,
        on_delete,
        parent=None,
    ):
        super().__init__(parent)

        self.study_session = study_session
        self.course_name = course_name

        self.on_edit = on_edit
        self.on_delete = on_delete

        self.setObjectName(
            "dataCard"
        )

        self.setup_ui()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        layout.setSpacing(
            10
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title_layout.setSpacing(
            4
        )

        course_label = QLabel(
            f"📚 {self.course_name}"
        )

        course_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            """
        )

        date_label = QLabel(
            f"📅 {format_date(self.study_session.study_date)}"
        )

        date_label.setObjectName(
            "subtitle"
        )

        title_layout.addWidget(
            course_label
        )

        title_layout.addWidget(
            date_label
        )

        header.addLayout(
            title_layout,
            stretch=1,
        )

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        total_minutes = (
            self.study_session.duration_minutes
        )

        duration_text = (
            f"⏱ {format_duration(total_minutes)}"
        )

        duration_label = QLabel(
            duration_text
        )

        duration_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            """
        )

        header.addWidget(
            duration_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        if self.study_session.notes:

            notes_title = QLabel(
                tr("Study Notes")
            )

            notes_title.setStyleSheet(
                """
                font-weight: 600;
                """
            )

            layout.addWidget(
                notes_title
            )

            notes = QLabel(
                self.study_session.notes
            )

            notes.setObjectName(
                "subtitle"
            )

            notes.setWordWrap(
                True
            )

            layout.addWidget(
                notes
            )

        layout.addSpacing(
            4
        )

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        actions = QHBoxLayout()

        edit_button = SecondaryButton(
            tr("✏ Edit")
        )

        edit_button.clicked.connect(
            lambda:
            self.on_edit(
                self.study_session
            )
        )

        delete_button = DangerButton(
            tr("🗑 Delete")
        )

        delete_button.clicked.connect(
            lambda:
            self.on_delete(
                self.study_session
            )
        )

        actions.addStretch()

        actions.addWidget(
            edit_button
        )

        actions.addWidget(
            delete_button
        )

        layout.addLayout(
            actions
        )


class StudySessionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.sessions = []
        self.courses = []

        self.setup_ui()
        self.refresh_data()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            scroll_area
        )

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            36,
            30,
            36,
            30,
        )

        layout.setSpacing(
            20
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        add_button = PrimaryButton(
            "＋ Log Study Session"
        )

        add_button.clicked.connect(
            self.add_session
        )

        header = PageHeader(
            "Study Sessions",
            (
                "Track your study time and "
                "review your learning activity."
            ),
            add_button,
        )

        layout.addWidget(
            header
        )

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        self.stats_label = QLabel()

        self.stats_label.setObjectName(
            "subtitle"
        )

        layout.addWidget(
            self.stats_label
        )

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        filters = QHBoxLayout()

        filters.setSpacing(
            10
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "🔍 Search study notes..."
        )

        self.search_input.textChanged.connect(
            self.apply_filters
        )

        self.course_filter = QComboBox()

        add_combo_item(
            self.course_filter,
            "All Courses",
            None,
        )

        self.course_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.date_filter = QLineEdit()

        self.date_filter.setPlaceholderText(
            "Filter by date..."
        )

        self.date_filter.textChanged.connect(
            self.apply_filters
        )

        refresh_button = SecondaryButton(
            "↻ Refresh"
        )

        refresh_button.clicked.connect(
            self.refresh_data
        )

        filters.addWidget(
            self.search_input,
            stretch=1,
        )

        filters.addWidget(
            self.course_filter
        )

        filters.addWidget(
            self.date_filter
        )

        filters.addWidget(
            refresh_button
        )

        layout.addLayout(
            filters
        )

        # ----------------------------------------------------
        # LIST
        # ----------------------------------------------------

        self.sessions_container = QWidget()

        self.sessions_layout = QVBoxLayout(
            self.sessions_container
        )

        self.sessions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.sessions_layout.setSpacing(
            14
        )

        layout.addWidget(
            self.sessions_container
        )

        layout.addStretch()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_data(self):
        try:
            self.sessions = (
                get_all_study_sessions()
            )

            self.courses = (
                get_all_courses()
            )

        except Exception as error:
            show_error(
                self,
                "Unable to load study sessions",
                str(error),
            )

            return

        self.populate_course_filter()
        self.update_statistics()
        self.apply_filters()

    # ========================================================
    # COURSE FILTER
    # ========================================================

    def populate_course_filter(self):
        current_course = (
            self.course_filter.currentData()
        )

        self.course_filter.blockSignals(
            True
        )

        self.course_filter.clear()

        add_combo_item(
            self.course_filter,
            "All Courses",
            None,
        )

        for course in self.courses:
            self.course_filter.addItem(
                course.name,
                course.id,
            )

        for index in range(
            self.course_filter.count()
        ):
            if (
                self.course_filter.itemData(index)
                == current_course
            ):
                self.course_filter.setCurrentIndex(
                    index
                )
                break

        self.course_filter.blockSignals(
            False
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def update_statistics(self):
        session_count = len(
            self.sessions
        )

        total_minutes = sum(
            session.duration_minutes
            for session in self.sessions
        )

        self.stats_label.setText(
            trf(
                "📊 {count} sessions   •   ⏱ {duration} studied",
                count=localize_digits(session_count),
                duration=format_duration(total_minutes),
            )
        )

    # ========================================================
    # FILTER
    # ========================================================

    def apply_filters(self):
        search_text = (
            self.search_input.text()
            .strip()
            .lower()
        )

        selected_course = (
            self.course_filter.currentData()
        )

        date_text = (
            self.date_filter.text()
            .strip()
            .lower()
        )

        filtered = []

        for session in self.sessions:

            notes = (
                session.notes or ""
            ).lower()

            if (
                search_text
                and search_text not in notes
            ):
                continue

            if (
                selected_course is not None
                and session.course_id
                != selected_course
            ):
                continue

            if (
                date_text
                and date_text
                not in session.study_date.lower()
            ):
                continue

            filtered.append(
                session
            )

        self.render_sessions(
            filtered
        )

    # ========================================================
    # RENDER
    # ========================================================

    def render_sessions(
        self,
        sessions,
    ):
        self.clear_sessions()

        if not sessions:

            empty = EmptyState(
                icon="⏱",
                title=tr("No study sessions found"),
                message=tr(
                    "Log your first study session "
                    "or change the filters."
                ),
            )

            empty.setMinimumHeight(
                280
            )

            self.sessions_layout.addWidget(
                empty
            )

            return

        course_names = {
            course.id: course.name
            for course in self.courses
        }

        for session in sessions:

            course_name = course_names.get(
                session.course_id,
                tr("Unknown Course"),
            )

            card = StudySessionCard(
                study_session=session,
                course_name=course_name,
                on_edit=self.edit_session,
                on_delete=self.delete_session,
            )

            self.sessions_layout.addWidget(
                card
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_sessions(self):
        while self.sessions_layout.count():

            item = (
                self.sessions_layout.takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ========================================================
    # ADD
    # ========================================================

    def add_session(self):
        active_courses = [
            course
            for course in self.courses
            if course.is_active
        ]

        if not active_courses:
            show_error(
                self,
                "No active courses",
                (
                    "Create an active course before "
                    "logging a study session."
                ),
            )

            return

        dialog = StudySessionDialog(
            parent=self
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            create_study_session(
                course_id=data["course_id"],
                study_date=data["study_date"],
                duration_minutes=data[
                    "duration_minutes"
                ],
                notes=data["notes"],
            )

        except Exception as error:
            show_error(
                self,
                "Unable to create study session",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_session(self, session):
        dialog = StudySessionDialog(
            study_session=session,
            parent=self,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            updated = update_study_session(
                session_id=session.id,
                course_id=data["course_id"],
                study_date=data["study_date"],
                duration_minutes=data[
                    "duration_minutes"
                ],
                notes=data["notes"],
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    (
                        "The study session could not "
                        "be updated."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to update study session",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_session(self, session):
        confirmed = confirm_delete(
            self,
            "Delete Study Session",
            trf(
                'Delete the study session for "{date}"?'
                "\n\nThis action cannot be undone.",
                date=format_date(session.study_date),
            ),
        )

        if not confirmed:
            return

        try:
            deleted = delete_study_session(
                session.id
            )

            if not deleted:
                show_error(
                    self,
                    "Delete failed",
                    (
                        "The study session could not "
                        "be deleted."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to delete study session",
                str(error),
            )

            return

        self.refresh_data()