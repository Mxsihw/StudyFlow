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
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from constants import (
    ASSIGNMENT_PRIORITIES,
    ASSIGNMENT_STATUSES,
)

from gui.i18n import (
    add_combo_item,
    add_combo_items,
    format_date,
    localize_digits,
    select_combo_data,
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
    create_assignment,
    delete_assignment,
    get_all_assignments,
    get_all_courses,
    update_assignment,
)


class AssignmentDialog(QDialog):
    def __init__(
        self,
        assignment=None,
        parent=None,
    ):
        super().__init__(parent)

        self.assignment = assignment
        self.courses = []

        self.setWindowTitle(
            "Add Assignment"
            if assignment is None
            else "Edit Assignment"
        )

        self.setMinimumWidth(480)

        self.setup_ui()
        self.load_courses()

        if assignment is not None:
            self.load_assignment_data()

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
        # TITLE
        # ----------------------------------------------------

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Example: Database Project"
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Optional description..."
        )

        self.description_input.setFixedHeight(90)

        # ----------------------------------------------------
        # DEADLINE
        # ----------------------------------------------------

        self.deadline_input = QLineEdit()

        self.deadline_input.setPlaceholderText(
            "YYYY-MM-DD or Jalali date"
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_input = QComboBox()

        add_combo_items(
            self.status_input,
            ASSIGNMENT_STATUSES,
        )

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        self.priority_input = QComboBox()

        add_combo_items(
            self.priority_input,
            ASSIGNMENT_PRIORITIES,
        )

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        self.progress_input = QSpinBox()

        self.progress_input.setRange(
            0,
            100,
        )

        self.progress_input.setSuffix(
            tr("%")
        )

        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        form.addRow(
            "Course *",
            self.course_input,
        )

        form.addRow(
            "Title *",
            self.title_input,
        )

        form.addRow(
            "Description",
            self.description_input,
        )

        form.addRow(
            "Deadline",
            self.deadline_input,
        )

        form.addRow(
            "Status",
            self.status_input,
        )

        form.addRow(
            "Priority",
            self.priority_input,
        )

        form.addRow(
            "Progress",
            self.progress_input,
        )

        layout.addLayout(form)

        layout.addSpacing(10)

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

        layout.addWidget(buttons)

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
    # LOAD EDIT DATA
    # ========================================================

    def load_assignment_data(self):
        assignment = self.assignment

        self.title_input.setText(
            assignment.title
        )

        self.description_input.setPlainText(
            assignment.description or ""
        )

        self.deadline_input.setText(
            assignment.deadline or ""
        )

        select_combo_data(
            self.status_input,
            assignment.status,
        )

        select_combo_data(
            self.priority_input,
            assignment.priority,
        )

        self.progress_input.setValue(
            assignment.progress
        )

        for index in range(
            self.course_input.count()
        ):
            if (
                self.course_input.itemData(index)
                == assignment.course_id
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
                "Please create and select a course first.",
            )
            return

        if not self.title_input.text().strip():
            show_error(
                self,
                "Title required",
                "Please enter an assignment title.",
            )
            return

        self.accept()

    # ========================================================
    # DATA
    # ========================================================

    def get_data(self):
        description = (
            self.description_input
            .toPlainText()
            .strip()
        )

        deadline = (
            self.deadline_input
            .text()
            .strip()
        )

        return {
            "course_id":
                self.course_input.currentData(),

            "title":
                self.title_input.text().strip(),

            "description":
                description or None,

            "deadline":
                deadline or None,

            "status":
                self.status_input.currentData(),

            "priority":
                self.priority_input.currentData(),

            "progress":
                self.progress_input.value(),
        }


class AssignmentCard(QFrame):
    def __init__(
        self,
        assignment,
        course_name,
        on_edit,
        on_delete,
        on_status_change,
        parent=None,
    ):
        super().__init__(parent)

        self.assignment = assignment
        self.course_name = course_name

        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_status_change = (
            on_status_change
        )

        self.setObjectName("dataCard")

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

        layout.setSpacing(10)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title_layout.setSpacing(3)

        title = QLabel(
            self.assignment.title
        )

        title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            """
        )

        course = QLabel(
            f"📚 {self.course_name}"
        )

        course.setObjectName(
            "subtitle"
        )

        title_layout.addWidget(title)
        title_layout.addWidget(course)

        header.addLayout(
            title_layout,
            stretch=1,
        )

        priority = QLabel(
            trf(
                "🔥 {priority}",
                priority=tr(self.assignment.priority),
            )
        )

        priority.setObjectName(
            "subtitle"
        )

        header.addWidget(
            priority,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(header)

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        if self.assignment.description:
            description = QLabel(
                self.assignment.description
            )

            description.setWordWrap(True)

            description.setObjectName(
                "subtitle"
            )

            layout.addWidget(description)

        # ----------------------------------------------------
        # DEADLINE
        # ----------------------------------------------------

        deadline_text = (
            format_date(self.assignment.deadline)
            if self.assignment.deadline
            else tr("No deadline")
        )

        deadline = QLabel(
            trf(
                "📅 Deadline: {deadline}",
                deadline=deadline_text,
            )
        )

        deadline.setObjectName(
            "subtitle"
        )

        layout.addWidget(deadline)

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        progress_layout = QHBoxLayout()

        progress_label = QLabel(
            trf(
                "Progress: {progress}%",
                progress=localize_digits(
                    self.assignment.progress
                ),
            )
        )

        progress_label.setObjectName(
            "subtitle"
        )

        progress_layout.addWidget(
            progress_label
        )

        progress_layout.addStretch()

        layout.addLayout(progress_layout)

        progress_bar = QProgressBar()

        progress_bar.setRange(
            0,
            100,
        )

        progress_bar.setValue(
            self.assignment.progress
        )

        progress_bar.setTextVisible(False)

        progress_bar.setFixedHeight(8)

        layout.addWidget(progress_bar)

        layout.addSpacing(4)

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        actions = QHBoxLayout()

        status_combo = QComboBox()

        add_combo_items(
            status_combo,
            ASSIGNMENT_STATUSES,
        )

        select_combo_data(
            status_combo,
            self.assignment.status,
        )

        status_combo.currentIndexChanged.connect(
            lambda _index:
            self.change_status(
                status_combo.currentData()
            )
        )

        edit_button = SecondaryButton(
            tr("✏ Edit")
        )

        edit_button.clicked.connect(
            lambda:
            self.on_edit(
                self.assignment
            )
        )

        delete_button = DangerButton(
            tr("🗑 Delete")
        )

        delete_button.clicked.connect(
            lambda:
            self.on_delete(
                self.assignment
            )
        )

        actions.addWidget(
            status_combo
        )

        actions.addStretch()

        actions.addWidget(
            edit_button
        )

        actions.addWidget(
            delete_button
        )

        layout.addLayout(actions)

    # ========================================================
    # QUICK STATUS CHANGE
    # ========================================================

    def change_status(self, new_status):
        if new_status == self.assignment.status:
            return

        self.on_status_change(
            self.assignment,
            new_status,
        )


class AssignmentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.assignments = []
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

        scroll_area.setWidgetResizable(True)

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        scroll_area.setWidget(content)

        root_layout.addWidget(
            scroll_area
        )

        layout = QVBoxLayout(content)

        layout.setContentsMargins(
            36,
            30,
            36,
            30,
        )

        layout.setSpacing(20)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        add_button = PrimaryButton(
            "＋ Add Assignment"
        )

        add_button.clicked.connect(
            self.add_assignment
        )

        header = PageHeader(
            "Assignments",
            (
                "Track your tasks, deadlines "
                "and study progress."
            ),
            add_button,
        )

        layout.addWidget(header)

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        filters = QHBoxLayout()

        filters.setSpacing(10)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "🔍 Search assignments..."
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

        self.status_filter = QComboBox()

        add_combo_item(
            self.status_filter,
            "All Statuses",
            None,
        )

        add_combo_items(
            self.status_filter,
            ASSIGNMENT_STATUSES,
        )

        self.status_filter.currentIndexChanged.connect(
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
            self.status_filter
        )

        filters.addWidget(
            refresh_button
        )

        layout.addLayout(filters)

        # ----------------------------------------------------
        # ASSIGNMENTS CONTAINER
        # ----------------------------------------------------

        self.assignments_container = QWidget()

        self.assignments_layout = QVBoxLayout(
            self.assignments_container
        )

        self.assignments_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.assignments_layout.setSpacing(14)

        layout.addWidget(
            self.assignments_container
        )

        layout.addStretch()

    # ========================================================
    # REFRESH DATA
    # ========================================================

    def refresh_data(self):
        try:
            self.courses = get_all_courses()

            self.assignments = (
                get_all_assignments()
            )

        except Exception as error:
            show_error(
                self,
                "Unable to load assignments",
                str(error),
            )

            return

        self.populate_course_filter()

        self.apply_filters()

    # ========================================================
    # COURSE FILTER
    # ========================================================

    def populate_course_filter(self):
        current_course = (
            self.course_filter.currentData()
        )

        self.course_filter.blockSignals(True)

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

        self.course_filter.blockSignals(False)

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

        selected_status = (
            self.status_filter.currentData()
        )

        filtered = []

        for assignment in self.assignments:

            # Search
            searchable = " ".join(
                [
                    assignment.title or "",
                    assignment.description or "",
                ]
            ).lower()

            if (
                search_text
                and search_text not in searchable
            ):
                continue

            # Course
            if (
                selected_course is not None
                and assignment.course_id
                != selected_course
            ):
                continue

            # Status
            if (
                selected_status is not None
                and assignment.status
                != selected_status
            ):
                continue

            filtered.append(
                assignment
            )

        self.render_assignments(
            filtered
        )

    # ========================================================
    # RENDER
    # ========================================================

    def render_assignments(
        self,
        assignments,
    ):
        self.clear_assignments()

        if not assignments:
            empty = EmptyState(
                icon="📝",
                title=tr("No assignments found"),
                message=tr(
                    "Add a new assignment or "
                    "change your filters."
                ),
            )

            empty.setMinimumHeight(280)

            self.assignments_layout.addWidget(
                empty
            )

            return

        course_names = {
            course.id: course.name
            for course in self.courses
        }

        for assignment in assignments:
            course_name = course_names.get(
                assignment.course_id,
                tr("Unknown Course"),
            )

            card = AssignmentCard(
                assignment=assignment,
                course_name=course_name,
                on_edit=self.edit_assignment,
                on_delete=self.delete_assignment,
                on_status_change=(
                    self.quick_change_status
                ),
            )

            self.assignments_layout.addWidget(
                card
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_assignments(self):
        while self.assignments_layout.count():
            item = (
                self.assignments_layout.takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ========================================================
    # ADD
    # ========================================================

    def add_assignment(self):
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
                    "adding an assignment."
                ),
            )

            return

        dialog = AssignmentDialog(
            parent=self
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            create_assignment(
                course_id=data["course_id"],
                title=data["title"],
                description=data["description"],
                deadline=data["deadline"],
                status=data["status"],
                priority=data["priority"],
                progress=data["progress"],
            )

        except Exception as error:
            show_error(
                self,
                "Unable to create assignment",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_assignment(self, assignment):
        dialog = AssignmentDialog(
            assignment=assignment,
            parent=self,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            updated = update_assignment(
                assignment_id=assignment.id,
                course_id=data["course_id"],
                title=data["title"],
                description=data["description"],
                deadline=data["deadline"],
                status=data["status"],
                priority=data["priority"],
                progress=data["progress"],
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    (
                        "The assignment could not "
                        "be updated."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to update assignment",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # QUICK STATUS
    # ========================================================

    def quick_change_status(
        self,
        assignment,
        new_status,
    ):
        progress = assignment.progress

        if new_status == "Completed":
            progress = 100

        try:
            updated = update_assignment(
                assignment_id=assignment.id,
                status=new_status,
                progress=progress,
            )

            if not updated:
                return

        except Exception as error:
            show_error(
                self,
                "Unable to update status",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_assignment(self, assignment):
        confirmed = confirm_delete(
            self,
            "Delete Assignment",
            trf(
                'Are you sure you want to delete "{name}"?'
                "\n\nThis action cannot be undone.",
                name=assignment.title,
            ),
        )

        if not confirmed:
            return

        try:
            deleted = delete_assignment(
                assignment.id
            )

            if not deleted:
                show_error(
                    self,
                    "Delete failed",
                    (
                        "The assignment could not "
                        "be deleted."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to delete assignment",
                str(error),
            )

            return

        self.refresh_data()