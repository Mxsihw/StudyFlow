from datetime import date, datetime

try:
    import jdatetime
except ImportError:
    jdatetime = None

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import (
    format_date,
    localize_digits,
    tr,
    trf,
)

from gui.widgets import EmptyState, ScrollablePage

from services import (
    get_all_assignments,
    get_all_courses,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.scroll_page = ScrollablePage()

        root_layout.addWidget(
            self.scroll_page
        )

        layout = self.scroll_page.content_layout

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")

        subtitle = QLabel(
            "Here's an overview of your study progress."
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(self.title_label)
        layout.addWidget(subtitle)

        self.update_greeting()

        layout.addSpacing(6)

        # ----------------------------------------------------
        # STAT CARDS
        # ----------------------------------------------------

        stats_layout = QGridLayout()

        stats_layout.setSpacing(16)

        self.today_tasks_card = self.create_stat_card(
            "📌",
            "Today's Tasks",
            "0",
        )

        self.upcoming_card = self.create_stat_card(
            "⏳",
            "Upcoming Deadlines",
            "0",
        )

        self.active_courses_card = self.create_stat_card(
            "📚",
            "Active Courses",
            "0",
        )

        self.progress_card = self.create_stat_card(
            "📈",
            "Overall Progress",
            "0%",
        )

        stats_layout.addWidget(
            self.today_tasks_card["card"],
            0,
            0,
        )

        stats_layout.addWidget(
            self.upcoming_card["card"],
            0,
            1,
        )

        stats_layout.addWidget(
            self.active_courses_card["card"],
            1,
            0,
        )

        stats_layout.addWidget(
            self.progress_card["card"],
            1,
            1,
        )

        layout.addLayout(stats_layout)

        # ----------------------------------------------------
        # BOTTOM SECTION
        # ----------------------------------------------------

        bottom_layout = QHBoxLayout()

        bottom_layout.setSpacing(16)

        self.today_section = self.create_content_section(
            "Today's Tasks"
        )

        self.deadlines_section = self.create_content_section(
            "Upcoming Deadlines"
        )

        bottom_layout.addWidget(
            self.today_section,
            stretch=1,
        )

        bottom_layout.addWidget(
            self.deadlines_section,
            stretch=1,
        )

        layout.addLayout(bottom_layout)

        layout.addStretch()

    # ========================================================
    # STAT CARD
    # ========================================================

    def create_stat_card(
        self,
        icon,
        label,
        value,
    ):
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(145)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )

        icon_label = QLabel(icon)
        icon_label.setObjectName("cardIcon")

        label_widget = QLabel(label)
        label_widget.setObjectName("cardLabel")

        value_widget = QLabel(value)
        value_widget.setObjectName("statValue")

        layout.addWidget(icon_label)

        layout.addStretch()

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return {
            "card": card,
            "value": value_widget,
        }

    # ========================================================
    # CONTENT SECTION
    # ========================================================

    def create_content_section(self, title):
        section = QFrame()
        section.setObjectName("contentCard")

        section.setMinimumHeight(260)

        layout = QVBoxLayout(section)

        layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")

        layout.addWidget(title_label)

        container = QWidget()

        container_layout = QVBoxLayout(container)

        container_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        layout.addWidget(container)

        return section

    # ========================================================
    # REFRESH DATA
    # ========================================================

    def refresh_data(self):
        self.update_greeting()

        try:
            courses = get_all_courses()

            assignments = get_all_assignments()

        except Exception:
            return

        active_courses = [
            course
            for course in courses
            if course.is_active
        ]

        today_assignments = [
            assignment
            for assignment in assignments
            if self.is_today(
                assignment.deadline
            )
            and not self.is_completed(
                assignment.status
            )
        ]

        upcoming_assignments = [
            assignment
            for assignment in assignments
            if assignment.deadline
            and not self.is_completed(
                assignment.status
            )
        ]

        overall_progress = (
            self.calculate_progress(
                assignments
            )
        )

        self.today_tasks_card["value"].setText(
            localize_digits(len(today_assignments))
        )

        self.upcoming_card["value"].setText(
            localize_digits(len(upcoming_assignments))
        )

        self.active_courses_card["value"].setText(
            localize_digits(len(active_courses))
        )

        self.progress_card["value"].setText(
            f"{localize_digits(overall_progress)}%"
        )

        self.update_today_tasks(
            today_assignments
        )

        self.update_upcoming_deadlines(
            upcoming_assignments[:5],
            courses,
        )

    # ========================================================
    # TODAY TASKS
    # ========================================================

    def update_today_tasks(self, assignments):
        layout = self.today_section.layout()

        self.clear_layout(
            layout,
            keep_first=True,
        )

        if not assignments:
            empty = EmptyState(
                icon="🎉",
                title=tr("No tasks for today"),
                message=tr(
                    "You're all caught up for today."
                ),
            )

            layout.addWidget(
                empty,
                stretch=1,
            )

            return

        for assignment in assignments[:5]:
            item = self.create_assignment_item(
                assignment.title,
                (
                    format_date(assignment.deadline)
                    if assignment.deadline
                    else tr("No deadline")
                ),
                tr(assignment.priority),
            )

            layout.addWidget(item)

        layout.addStretch()

    # ========================================================
    # UPCOMING DEADLINES
    # ========================================================

    def update_upcoming_deadlines(
        self,
        assignments,
        courses,
    ):
        layout = self.deadlines_section.layout()

        self.clear_layout(
            layout,
            keep_first=True,
        )

        if not assignments:
            empty = EmptyState(
                icon="📅",
                title=tr("No upcoming deadlines"),
                message=tr(
                    "Add an assignment with a deadline."
                ),
            )

            layout.addWidget(
                empty,
                stretch=1,
            )

            return

        course_names = {
            course.id: course.name
            for course in courses
        }

        for assignment in assignments:
            course_name = course_names.get(
                assignment.course_id,
                tr("Unknown Course"),
            )

            item = self.create_deadline_item(
                assignment.title,
                course_name,
                (
                    format_date(assignment.deadline)
                    if assignment.deadline
                    else tr("No deadline")
                ),
            )

            layout.addWidget(item)

        layout.addStretch()

    # ========================================================
    # ASSIGNMENT ITEM
    # ========================================================

    def create_assignment_item(
        self,
        title,
        deadline,
        priority,
    ):
        item = QFrame()
        item.setObjectName("dataCard")

        layout = QVBoxLayout(item)

        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        title_label = QLabel(title)

        title_label.setStyleSheet(
            "font-weight: 600;"
        )

        details = QLabel(
            trf(
                "Deadline: {deadline}   •   Priority: {priority}",
                deadline=deadline or tr("No deadline"),
                priority=priority,
            )
        )

        details.setObjectName("subtitle")

        layout.addWidget(title_label)
        layout.addWidget(details)

        return item

    # ========================================================
    # DEADLINE ITEM
    # ========================================================

    def create_deadline_item(
        self,
        title,
        course_name,
        deadline,
    ):
        item = QFrame()
        item.setObjectName("dataCard")

        layout = QVBoxLayout(item)

        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        title_label = QLabel(title)

        title_label.setStyleSheet(
            "font-weight: 600;"
        )

        details = QLabel(
            trf(
                "{course}   •   {deadline}",
                course=course_name,
                deadline=deadline,
            )
        )

        details.setObjectName("subtitle")

        layout.addWidget(title_label)
        layout.addWidget(details)

        return item

    # ========================================================
    # HELPERS
    # ========================================================

    def update_greeting(self):
        if hasattr(self, "title_label"):
            self.title_label.setText(
                f"{tr(self.get_greeting())} 👋"
            )

    def get_greeting(self):
        hour = datetime.now().hour

        if hour < 12:
            return "Good Morning"

        if hour < 18:
            return "Good Afternoon"

        return "Good Evening"

    def is_completed(self, status):
        if not status:
            return False

        return (
            status.strip().lower()
            == "completed"
        )

    def is_today(self, deadline):
        if not deadline:
            return False

        deadline = str(deadline).strip()

        today_gregorian = (
            date.today().isoformat()
        )

        if deadline == today_gregorian:
            return True

        if jdatetime is not None:
            today_jalali = jdatetime.date.today()

            jalali_values = {
                str(today_jalali),
                (
                    f"{today_jalali.year:04d}-"
                    f"{today_jalali.month:02d}-"
                    f"{today_jalali.day:02d}"
                ),
            }

            if deadline in jalali_values:
                return True

        return False

    def calculate_progress(self, assignments):
        if not assignments:
            return 0

        total_progress = sum(
            assignment.progress
            for assignment in assignments
        )

        return round(
            total_progress
            / len(assignments)
        )

    def clear_layout(
        self,
        layout,
        keep_first=False,
    ):
        start_index = 1 if keep_first else 0

        while layout.count() > start_index:
            item = layout.takeAt(start_index)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()