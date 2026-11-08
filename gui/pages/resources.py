import webbrowser

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from constants import RESOURCE_STATUSES

from gui.i18n import (
    add_combo_item,
    add_combo_items,
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
    create_resource,
    delete_resource,
    get_all_courses,
    get_all_resources,
    update_resource,
)


RESOURCE_TYPES = (
    "Book",
    "PDF",
    "Article",
    "Video",
    "Website",
    "Notes",
    "Other",
)


class ResourceDialog(QDialog):
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)

        self.resource = resource
        self.courses = []

        if resource is None:
            self.setWindowTitle("Add Resource")
        else:
            self.setWindowTitle("Edit Resource")

        self.setMinimumWidth(520)

        self.setup_ui()
        self.load_courses()

        if self.resource is not None:
            self.load_resource_data()

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

        self.course_input.addItem(
            tr("No Course"),
            None,
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Example: Operating Systems Book"
        )

        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        self.type_input = QComboBox()

        add_combo_items(
            self.type_input,
            RESOURCE_TYPES,
        )

        # ----------------------------------------------------
        # AUTHOR
        # ----------------------------------------------------

        self.author_input = QLineEdit()

        self.author_input.setPlaceholderText(
            "Optional author name"
        )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        self.category_input = QLineEdit()

        self.category_input.setPlaceholderText(
            "Example: Reference"
        )

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText(
            "https://..."
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_input = QComboBox()

        add_combo_items(
            self.status_input,
            RESOURCE_STATUSES,
        )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        self.notes_input = QTextEdit()

        self.notes_input.setPlaceholderText(
            "Optional notes..."
        )

        self.notes_input.setFixedHeight(100)

        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        form.addRow(
            "Course",
            self.course_input,
        )

        form.addRow(
            "Title *",
            self.title_input,
        )

        form.addRow(
            "Type *",
            self.type_input,
        )

        form.addRow(
            "Author",
            self.author_input,
        )

        form.addRow(
            "Category",
            self.category_input,
        )

        form.addRow(
            "URL",
            self.url_input,
        )

        form.addRow(
            "Status",
            self.status_input,
        )

        form.addRow(
            "Notes",
            self.notes_input,
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

        for course in self.courses:
            self.course_input.addItem(
                course.name,
                course.id,
            )

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_resource_data(self):
        resource = self.resource

        self.title_input.setText(
            resource.title
        )

        select_combo_data(
            self.type_input,
            resource.resource_type,
        )

        self.author_input.setText(
            resource.author or ""
        )

        self.category_input.setText(
            resource.category or ""
        )

        self.url_input.setText(
            resource.url or ""
        )

        select_combo_data(
            self.status_input,
            resource.status,
        )

        self.notes_input.setPlainText(
            resource.notes or ""
        )

        for index in range(
            self.course_input.count()
        ):
            if (
                self.course_input.itemData(index)
                == resource.course_id
            ):
                self.course_input.setCurrentIndex(
                    index
                )
                break

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_and_accept(self):
        if not self.title_input.text().strip():
            show_error(
                self,
                "Title required",
                "Please enter a resource title.",
            )

            return

        if not self.type_input.currentData():
            show_error(
                self,
                "Type required",
                "Please select a resource type.",
            )

            return

        self.accept()

    # ========================================================
    # DATA
    # ========================================================

    def get_data(self):
        author = self.author_input.text().strip()
        category = self.category_input.text().strip()
        url = self.url_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        return {
            "course_id":
                self.course_input.currentData(),

            "title":
                self.title_input.text().strip(),

            "resource_type":
                self.type_input.currentData(),

            "author":
                author or None,

            "category":
                category or None,

            "url":
                url or None,

            "status":
                self.status_input.currentData(),

            "notes":
                notes or None,
        }


class ResourceCard(QFrame):
    def __init__(
        self,
        resource,
        course_name,
        on_edit,
        on_delete,
        on_status_change,
        parent=None,
    ):
        super().__init__(parent)

        self.resource = resource
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
        title_layout.setSpacing(4)

        title = QLabel(
            self.resource.title
        )

        title.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            """
        )

        title_layout.addWidget(title)

        type_label = QLabel(
            f"📄 {tr(self.resource.resource_type)}"
        )

        type_label.setObjectName(
            "subtitle"
        )

        title_layout.addWidget(
            type_label
        )

        header.addLayout(
            title_layout,
            stretch=1,
        )

        if self.resource.course_id:
            course_label = QLabel(
                f"📚 {self.course_name}"
            )
        else:
            course_label = QLabel(
                f"📁 {tr('General')}"
            )

        course_label.setObjectName(
            "subtitle"
        )

        header.addWidget(
            course_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addLayout(header)

        # ----------------------------------------------------
        # META INFORMATION
        # ----------------------------------------------------

        meta_items = []

        if self.resource.author:
            meta_items.append(
                f"👤 {self.resource.author}"
            )

        if self.resource.category:
            meta_items.append(
                f"🏷 {self.resource.category}"
            )

        if meta_items:
            meta = QLabel(
                "   •   ".join(meta_items)
            )

            meta.setObjectName(
                "subtitle"
            )

            meta.setWordWrap(True)

            layout.addWidget(meta)

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        if self.resource.url:
            url_button = SecondaryButton(
                tr("🌐 Open Resource")
            )

            url_button.clicked.connect(
                self.open_url
            )

            layout.addWidget(
                url_button,
                alignment=Qt.AlignmentFlag.AlignLeft,
            )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        if self.resource.notes:
            notes_title = QLabel(
                tr("Notes")
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
                self.resource.notes
            )

            notes.setWordWrap(True)

            notes.setObjectName(
                "subtitle"
            )

            layout.addWidget(
                notes
            )

        layout.addSpacing(4)

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        actions = QHBoxLayout()

        status_combo = QComboBox()

        add_combo_items(
            status_combo,
            RESOURCE_STATUSES,
        )

        select_combo_data(
            status_combo,
            self.resource.status,
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
            self.on_edit(self.resource)
        )

        delete_button = DangerButton(
            tr("🗑 Delete")
        )

        delete_button.clicked.connect(
            lambda:
            self.on_delete(self.resource)
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
    # OPEN URL
    # ========================================================

    def open_url(self):
        if self.resource.url:
            webbrowser.open(
                self.resource.url
            )

    # ========================================================
    # STATUS
    # ========================================================

    def change_status(self, new_status):
        if new_status == self.resource.status:
            return

        self.on_status_change(
            self.resource,
            new_status,
        )


class ResourcesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resources = []
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
            "＋ Add Resource"
        )

        add_button.clicked.connect(
            self.add_resource
        )

        header = PageHeader(
            "Resources",
            (
                "Organize your books, PDFs, "
                "links and study materials."
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
            "🔍 Search resources..."
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

        self.type_filter = QComboBox()

        add_combo_item(
            self.type_filter,
            "All Types",
            None,
        )

        add_combo_items(
            self.type_filter,
            RESOURCE_TYPES,
        )

        self.type_filter.currentIndexChanged.connect(
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
            RESOURCE_STATUSES,
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
            self.type_filter
        )

        filters.addWidget(
            self.status_filter
        )

        filters.addWidget(
            refresh_button
        )

        layout.addLayout(
            filters
        )

        # ----------------------------------------------------
        # RESOURCE LIST
        # ----------------------------------------------------

        self.resources_container = QWidget()

        self.resources_layout = QVBoxLayout(
            self.resources_container
        )

        self.resources_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.resources_layout.setSpacing(
            14
        )

        layout.addWidget(
            self.resources_container
        )

        layout.addStretch()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_data(self):
        try:
            self.resources = (
                get_all_resources()
            )

            self.courses = (
                get_all_courses()
            )

        except Exception as error:
            show_error(
                self,
                "Unable to load resources",
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
    # FILTERS
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

        selected_type = (
            self.type_filter.currentData()
        )

        selected_status = (
            self.status_filter.currentData()
        )

        filtered = []

        for resource in self.resources:

            searchable_text = " ".join(
                [
                    resource.title or "",
                    resource.resource_type or "",
                    resource.author or "",
                    resource.category or "",
                    resource.notes or "",
                ]
            ).lower()

            if (
                search_text
                and search_text
                not in searchable_text
            ):
                continue

            if (
                selected_course is not None
                and resource.course_id
                != selected_course
            ):
                continue

            if (
                selected_type is not None
                and resource.resource_type
                != selected_type
            ):
                continue

            if (
                selected_status is not None
                and resource.status
                != selected_status
            ):
                continue

            filtered.append(
                resource
            )

        self.render_resources(
            filtered
        )

    # ========================================================
    # RENDER
    # ========================================================

    def render_resources(
        self,
        resources,
    ):
        self.clear_resources()

        if not resources:
            empty = EmptyState(
                icon="📁",
                title=tr("No resources found"),
                message=tr(
                    "Add your first study resource "
                    "or change the filters."
                ),
            )

            empty.setMinimumHeight(
                280
            )

            self.resources_layout.addWidget(
                empty
            )

            return

        course_names = {
            course.id: course.name
            for course in self.courses
        }

        for resource in resources:

            course_name = course_names.get(
                resource.course_id,
                tr("General"),
            )

            card = ResourceCard(
                resource=resource,
                course_name=course_name,
                on_edit=self.edit_resource,
                on_delete=self.delete_resource,
                on_status_change=(
                    self.quick_change_status
                ),
            )

            self.resources_layout.addWidget(
                card
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_resources(self):
        while self.resources_layout.count():

            item = (
                self.resources_layout.takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ========================================================
    # ADD
    # ========================================================

    def add_resource(self):
        dialog = ResourceDialog(
            parent=self
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            create_resource(
                title=data["title"],
                resource_type=data[
                    "resource_type"
                ],
                course_id=data["course_id"],
                author=data["author"],
                category=data["category"],
                url=data["url"],
                status=data["status"],
                notes=data["notes"],
            )

        except Exception as error:
            show_error(
                self,
                "Unable to create resource",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_resource(self, resource):
        dialog = ResourceDialog(
            resource=resource,
            parent=self,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            updated = update_resource(
                resource_id=resource.id,
                title=data["title"],
                resource_type=data[
                    "resource_type"
                ],
                course_id=data["course_id"],
                author=data["author"],
                category=data["category"],
                url=data["url"],
                status=data["status"],
                notes=data["notes"],
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    (
                        "The resource could not "
                        "be updated."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to update resource",
                str(error),
            )

            return

        self.refresh_data()

    # ========================================================
    # QUICK STATUS
    # ========================================================

    def quick_change_status(
        self,
        resource,
        new_status,
    ):
        try:
            updated = update_resource(
                resource_id=resource.id,
                status=new_status,
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

    def delete_resource(self, resource):
        confirmed = confirm_delete(
            self,
            "Delete Resource",
            trf(
                'Are you sure you want to delete "{name}"?'
                "\n\nThis action cannot be undone.",
                name=resource.title,
            ),
        )

        if not confirmed:
            return

        try:
            deleted = delete_resource(
                resource.id
            )

            if not deleted:
                show_error(
                    self,
                    "Delete failed",
                    (
                        "The resource could not "
                        "be deleted."
                    ),
                )

                return

        except Exception as error:
            show_error(
                self,
                "Unable to delete resource",
                str(error),
            )

            return

        self.refresh_data()