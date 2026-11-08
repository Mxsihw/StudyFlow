from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
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
    QVBoxLayout,
    QWidget,
)

from gui.i18n import (
    add_combo_item,
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
    show_info,
)

from services import (
    create_course,
    delete_course,
    get_all_courses,
    set_course_active,
    update_course,
)


class CourseDialog(QDialog):
    def __init__(
        self,
        course=None,
        parent=None,
    ):
        super().__init__(parent)

        self.course = course
        self.selected_color = (
            course.color
            if course is not None
            and course.color
            else "#3B82F6"
        )

        self.setWindowTitle(
            "Add Course"
            if course is None
            else "Edit Course"
        )

        self.setMinimumWidth(420)

        self.setup_ui()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        form.setSpacing(12)

        # Name
        self.name_input = QLineEdit()

        self.name_input.setPlaceholderText(
            "Example: Operating Systems"
        )

        # Instructor
        self.instructor_input = QLineEdit()

        self.instructor_input.setPlaceholderText(
            "Optional"
        )

        # Credits
        self.credits_input = QSpinBox()

        self.credits_input.setRange(
            0,
            100,
        )

        self.credits_input.setSpecialValueText(
            "Not specified"
        )

        # Semester
        self.semester_input = QLineEdit()

        self.semester_input.setPlaceholderText(
            "Example: Fall 2026"
        )

        # Color
        color_container = QWidget()

        color_layout = QHBoxLayout(
            color_container
        )

        color_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.color_preview = QLabel()

        self.color_preview.setFixedSize(
            42,
            32,
        )

        self.color_preview.setStyleSheet(
            f"""
            background-color: {self.selected_color};
            border-radius: 7px;
            """
        )

        self.color_button = SecondaryButton(
            "Choose Color"
        )

        self.color_button.clicked.connect(
            self.choose_color
        )

        color_layout.addWidget(
            self.color_preview
        )

        color_layout.addWidget(
            self.color_button
        )

        color_layout.addStretch()

        form.addRow(
            "Course name *",
            self.name_input,
        )

        form.addRow(
            "Instructor",
            self.instructor_input,
        )

        form.addRow(
            "Credits",
            self.credits_input,
        )

        form.addRow(
            "Semester",
            self.semester_input,
        )

        form.addRow(
            "Color",
            color_container,
        )

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox()

        self.cancel_button = buttons.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        self.save_button = buttons.addButton(
            "Save",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        self.save_button.setObjectName(
            "primaryButton"
        )

        buttons.rejected.connect(
            self.reject
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        layout.addSpacing(12)

        layout.addWidget(buttons)

        # Fill values for editing.
        if self.course is not None:
            self.name_input.setText(
                self.course.name
            )

            self.instructor_input.setText(
                self.course.instructor or ""
            )

            self.credits_input.setValue(
                self.course.credits or 0
            )

            self.semester_input.setText(
                self.course.semester or ""
            )

    # ========================================================
    # COLOR
    # ========================================================

    def choose_color(self):
        color = QColorDialog.getColor(
            QColor(self.selected_color),
            self,
            "Choose Course Color",
        )

        if not color.isValid():
            return

        self.selected_color = color.name()

        self.color_preview.setStyleSheet(
            f"""
            background-color: {self.selected_color};
            border-radius: 7px;
            """
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            show_error(
                self,
                "Course name required",
                "Please enter a course name.",
            )
            return

        self.accept()

    # ========================================================
    # DATA
    # ========================================================

    def get_data(self):
        credits = self.credits_input.value()

        return {
            "name": (
                self.name_input.text().strip()
            ),
            "instructor": (
                self.instructor_input.text().strip()
                or None
            ),
            "credits": (
                credits
                if credits > 0
                else None
            ),
            "semester": (
                self.semester_input.text().strip()
                or None
            ),
            "color": self.selected_color,
        }


class CourseCard(QFrame):
    def __init__(
        self,
        course,
        on_edit,
        on_archive,
        on_delete,
        parent=None,
    ):
        super().__init__(parent)

        self.course = course

        self.on_edit = on_edit
        self.on_archive = on_archive
        self.on_delete = on_delete

        self.setObjectName("dataCard")

        self.setMinimumHeight(180)

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

        # Header
        header = QHBoxLayout()

        color_indicator = QFrame()

        color_indicator.setFixedSize(
            12,
            40,
        )

        course_color = (
            self.course.color
            or "#3B82F6"
        )

        color_indicator.setStyleSheet(
            f"""
            background-color: {course_color};
            border-radius: 6px;
            """
        )

        title_layout = QVBoxLayout()

        title_layout.setSpacing(3)

        name = QLabel(
            self.course.name
        )

        name.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            """
        )

        status_text = (
            "Active"
            if self.course.is_active
            else "Archived"
        )

        status = QLabel(tr(status_text))

        status.setObjectName("subtitle")

        title_layout.addWidget(name)
        title_layout.addWidget(status)

        header.addWidget(
            color_indicator
        )

        header.addLayout(
            title_layout,
            stretch=1,
        )

        layout.addLayout(header)

        layout.addSpacing(10)

        # Details
        details = []

        if self.course.instructor:
            details.append(
                f"👤 {self.course.instructor}"
            )

        if self.course.credits is not None:
            details.append(
                trf(
                    "🎓 {count} credits",
                    count=localize_digits(
                        self.course.credits
                    ),
                )
            )

        if self.course.semester:
            details.append(
                f"📅 {self.course.semester}"
            )

        if details:
            details_label = QLabel(
                "   •   ".join(details)
            )

            details_label.setObjectName(
                "subtitle"
            )

            details_label.setWordWrap(True)

            layout.addWidget(
                details_label
            )

        else:
            details_label = QLabel(
                tr("No additional information")
            )

            details_label.setObjectName(
                "subtitle"
            )

            layout.addWidget(
                details_label
            )

        layout.addStretch()

        # Actions
        actions = QHBoxLayout()

        edit_button = SecondaryButton(
            tr("✏ Edit")
        )

        edit_button.clicked.connect(
            lambda:
            self.on_edit(self.course)
        )

        archive_text = (
            "📦 Archive"
            if self.course.is_active
            else "♻ Restore"
        )

        archive_button = SecondaryButton(
            tr(archive_text)
        )

        archive_button.clicked.connect(
            lambda:
            self.on_archive(self.course)
        )

        delete_button = DangerButton(
            tr("🗑 Delete")
        )

        delete_button.clicked.connect(
            lambda:
            self.on_delete(self.course)
        )

        actions.addWidget(edit_button)

        actions.addWidget(archive_button)

        actions.addStretch()

        actions.addWidget(delete_button)

        layout.addLayout(actions)


class CoursesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.all_courses = []

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

        # Scroll area
        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setObjectName("pageContainer")

        scroll_area.setWidget(content)

        root_layout.addWidget(scroll_area)

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
            "＋ Add Course"
        )

        add_button.clicked.connect(
            self.add_course
        )

        header = PageHeader(
            "Courses",
            "Manage your courses and organize your semester.",
            add_button,
        )

        layout.addWidget(header)

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        filters = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "🔍 Search courses..."
        )

        self.search_input.textChanged.connect(
            self.apply_filters
        )

        self.status_filter = QComboBox()

        add_combo_item(
            self.status_filter,
            "All Courses",
            "all",
        )

        add_combo_item(
            self.status_filter,
            "Active",
            "active",
        )

        add_combo_item(
            self.status_filter,
            "Archived",
            "archived",
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
            self.status_filter
        )

        filters.addWidget(
            refresh_button
        )

        layout.addLayout(filters)

        # ----------------------------------------------------
        # COURSES CONTAINER
        # ----------------------------------------------------

        self.courses_container = QWidget()

        self.courses_layout = QVBoxLayout(
            self.courses_container
        )

        self.courses_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.courses_layout.setSpacing(14)

        layout.addWidget(
            self.courses_container
        )

        layout.addStretch()

    # ========================================================
    # LOAD DATA
    # ========================================================

    def refresh_data(self):
        try:
            self.all_courses = get_all_courses()

        except Exception as error:
            show_error(
                self,
                "Unable to load courses",
                str(error),
            )

            return

        self.apply_filters()

    # ========================================================
    # FILTER
    # ========================================================

    def apply_filters(self):
        search_text = (
            self.search_input.text()
            .strip()
            .lower()
        )

        status_filter = (
            self.status_filter.currentData()
        )

        filtered_courses = []

        for course in self.all_courses:
            if search_text:
                searchable_text = " ".join(
                    [
                        course.name or "",
                        course.instructor or "",
                        course.semester or "",
                    ]
                ).lower()

                if (
                    search_text
                    not in searchable_text
                ):
                    continue

            if (
                status_filter == "active"
                and not course.is_active
            ):
                continue

            if (
                status_filter == "archived"
                and course.is_active
            ):
                continue

            filtered_courses.append(course)

        self.render_courses(
            filtered_courses
        )

    # ========================================================
    # RENDER
    # ========================================================

    def render_courses(self, courses):
        self.clear_courses()

        if not courses:
            empty = EmptyState(
                icon="📚",
                title=tr("No courses found"),
                message=tr(
                    "Add your first course or "
                    "change the current filters."
                ),
            )

            empty.setMinimumHeight(280)

            self.courses_layout.addWidget(
                empty
            )

            return

        for course in courses:
            card = CourseCard(
                course=course,
                on_edit=self.edit_course,
                on_archive=self.toggle_course_status,
                on_delete=self.delete_course,
            )

            self.courses_layout.addWidget(
                card
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_courses(self):
        while self.courses_layout.count():
            item = self.courses_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ========================================================
    # ADD COURSE
    # ========================================================

    def add_course(self):
        dialog = CourseDialog(
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            create_course(
                name=data["name"],
                instructor=data["instructor"],
                credits=data["credits"],
                semester=data["semester"],
                color=data["color"],
            )

        except Exception as error:
            show_error(
                self,
                "Unable to create course",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # EDIT COURSE
    # ========================================================

    def edit_course(self, course):
        dialog = CourseDialog(
            course=course,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            updated = update_course(
                course_id=course.id,
                name=data["name"],
                instructor=data["instructor"],
                credits=data["credits"],
                semester=data["semester"],
                color=data["color"],
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    "The course could not be updated.",
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to update course",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # ARCHIVE / RESTORE
    # ========================================================

    def toggle_course_status(self, course):
        new_status = not course.is_active

        try:
            updated = set_course_active(
                course.id,
                new_status,
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    "The course status could not be changed.",
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to update course",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_course(self, course):
        confirmed = confirm_delete(
            self,
            "Delete Course",
            trf(
                'Are you sure you want to delete "{name}"?'
                "\n\nThis action cannot be undone.",
                name=course.name,
            ),
        )

        if not confirmed:
            return

        try:
            deleted = delete_course(
                course.id
            )

            if not deleted:
                show_error(
                    self,
                    "Delete failed",
                    "The course could not be deleted.",
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to delete course",
                str(error),
            )

            return

        self.refresh_data()