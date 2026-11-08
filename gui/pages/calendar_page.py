from calendar import monthrange
from datetime import date, datetime, timedelta

try:
    import jdatetime
except ImportError:  # pragma: no cover - jdatetime is a GUI dependency
    jdatetime = None

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import (
    add_combo_item,
    add_combo_items,
    format_date,
    is_rtl,
    localize_digits,
    month_title,
    select_combo_data,
    tr,
    trf,
    weekday_headers,
)

from gui.widgets import (
    DangerButton,
    PageHeader,
    PrimaryButton,
    SecondaryButton,
    confirm_delete,
    show_error,
)

from services import (
    create_calendar_event,
    delete_calendar_event,
    get_all_calendar_events,
    get_all_courses,
    update_calendar_event,
)


EVENT_TYPES = (
    "Class",
    "Exam",
    "Assignment",
    "Study",
    "Meeting",
    "Personal",
    "Other",
)


# ============================================================
# HELPERS
# ============================================================

def event_date(event):
    """Return the Gregorian date on which *event* starts."""

    try:
        date_part = str(event.start_datetime).split()[0]
        return datetime.strptime(date_part, "%Y-%m-%d").date()
    except (AttributeError, IndexError, ValueError):
        return None


def event_time(event):
    """Return the display time of *event* (``HH:MM``) or an empty string."""

    parts = str(event.start_datetime).split()

    return parts[1] if len(parts) > 1 else ""


def _elide(text, limit=16):
    text = str(text or "")

    if len(text) <= limit:
        return text

    return text[: limit - 1].rstrip() + "…"


# ============================================================
# DIALOG
# ============================================================

class CalendarEventDialog(QDialog):
    def __init__(
        self,
        event=None,
        default_date=None,
        parent=None,
    ):
        super().__init__(parent)

        self.calendar_event = event
        self.default_date = default_date
        self.courses = []

        self.setWindowTitle(
            "Add Calendar Event"
            if event is None
            else "Edit Calendar Event"
        )

        self.setMinimumWidth(520)

        self.setup_ui()
        self.load_courses()

        if self.calendar_event is not None:
            self.load_event_data()
        elif self.default_date is not None:
            self.start_input.setText(
                f"{self.default_date.isoformat()} 09:00"
            )

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.course_input = QComboBox()

        add_combo_item(
            self.course_input,
            "No Course / General Event",
            None,
        )

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Example: Database Midterm Exam"
        )

        self.type_input = QComboBox()

        add_combo_items(
            self.type_input,
            EVENT_TYPES,
        )

        self.start_input = QLineEdit()

        self.start_input.setPlaceholderText(
            "YYYY-MM-DD HH:MM"
        )

        self.has_end_checkbox = QCheckBox(
            "Set an end date and time"
        )

        self.end_input = QLineEdit()

        self.end_input.setPlaceholderText(
            "YYYY-MM-DD HH:MM"
        )

        self.end_input.setEnabled(False)

        self.has_end_checkbox.toggled.connect(
            self.end_input.setEnabled
        )

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Optional description..."
        )

        self.description_input.setFixedHeight(110)

        form.addRow("Course", self.course_input)
        form.addRow("Title *", self.title_input)
        form.addRow("Event Type *", self.type_input)
        form.addRow("Start *", self.start_input)
        form.addRow("", self.has_end_checkbox)
        form.addRow("End", self.end_input)
        form.addRow("Description", self.description_input)

        layout.addLayout(form)

        layout.addSpacing(10)

        buttons = QDialogButtonBox()

        buttons.addButton(
            "Cancel",
            QDialogButtonBox.ButtonRole.RejectRole,
        )

        buttons.addButton(
            "Save",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.validate_and_accept)

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
    # LOAD EVENT DATA
    # ========================================================

    def load_event_data(self):
        event = self.calendar_event

        self.title_input.setText(event.title)

        select_combo_data(
            self.type_input,
            event.event_type,
        )

        self.start_input.setText(event.start_datetime)

        if event.end_datetime:
            self.has_end_checkbox.setChecked(True)
            self.end_input.setText(event.end_datetime)

        self.description_input.setPlainText(
            event.description or ""
        )

        for index in range(self.course_input.count()):
            if self.course_input.itemData(index) == event.course_id:
                self.course_input.setCurrentIndex(index)
                break

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        start_datetime = self.start_input.text().strip()

        if not title:
            show_error(
                self,
                "Title required",
                "Please enter an event title.",
            )
            return

        if not start_datetime:
            show_error(
                self,
                "Start date required",
                "Please enter the event start date and time.",
            )
            return

        if (
            self.has_end_checkbox.isChecked()
            and not self.end_input.text().strip()
        ):
            show_error(
                self,
                "End date required",
                (
                    "Enter an end date and time "
                    "or disable the end date."
                ),
            )
            return

        self.accept()

    # ========================================================
    # DATA
    # ========================================================

    def get_data(self):
        description = (
            self.description_input.toPlainText().strip()
        )

        end_datetime = None

        if self.has_end_checkbox.isChecked():
            end_datetime = (
                self.end_input.text().strip() or None
            )

        return {
            "course_id": self.course_input.currentData(),
            "title": self.title_input.text().strip(),
            "event_type": self.type_input.currentData(),
            "start_datetime": self.start_input.text().strip(),
            "end_datetime": end_datetime,
            "description": description or None,
        }


# ============================================================
# CALENDAR DAY CELL
# ============================================================

class CalendarDay(QFrame):
    clicked = Signal(object)

    def __init__(
        self,
        day_date,
        day_number,
        in_current_month,
        selected,
        is_today,
        events,
        parent=None,
    ):
        super().__init__(parent)

        self.day_date = day_date

        self.setObjectName("calendarDay")

        self.setProperty(
            "selected",
            "true" if selected else "false",
        )

        self.setProperty(
            "today",
            "true" if is_today else "false",
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(94)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(2)

        number = QLabel(
            localize_digits(day_number)
        )

        number.setObjectName("dayNumber")

        number.setProperty(
            "muted",
            "false" if in_current_month else "true",
        )

        number.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        layout.addWidget(number)

        for event in events[:2]:
            chip = QLabel(
                _elide(event.title)
            )

            chip.setObjectName("eventChip")

            chip.setToolTip(
                f"{event.title}\n{event.start_datetime}"
            )

            chip.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )

            layout.addWidget(chip)

        if len(events) > 2:
            more = QLabel(
                trf(
                    "+{count} more",
                    count=localize_digits(
                        len(events) - 2
                    ),
                )
            )

            more.setObjectName("eventChipMore")

            more.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )

            layout.addWidget(more)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.day_date)

        super().mousePressEvent(event)


# ============================================================
# PAGE
# ============================================================

class CalendarPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.events = []
        self.courses = []

        self.view_year = None
        self.view_month = None
        self.selected_date = date.today()

        self.set_view_to_date(self.selected_date)

        self.setup_ui()
        self.refresh_data()

    # ========================================================
    # CALENDAR VIEW HELPERS
    # ========================================================

    def set_view_to_date(self, value):
        """Set the displayed month so that *value* is visible."""

        if is_rtl() and jdatetime is not None:
            jalali = jdatetime.date.fromgregorian(date=value)

            self.view_year = jalali.year
            self.view_month = jalali.month

        else:
            self.view_year = value.year
            self.view_month = value.month

    def same_display_month(self, value):
        if is_rtl() and jdatetime is not None:
            jalali = jdatetime.date.fromgregorian(date=value)

            return (
                jalali.year == self.view_year
                and jalali.month == self.view_month
            )

        return (
            value.year == self.view_year
            and value.month == self.view_month
        )

    def first_day_of_view(self):
        if is_rtl() and jdatetime is not None:
            return jdatetime.date(
                self.view_year,
                self.view_month,
                1,
            ).togregorian()

        return date(
            self.view_year,
            self.view_month,
            1,
        )

    def month_context(self):
        """Return ``(first_date, day_count, leading_blanks)``."""

        if is_rtl() and jdatetime is not None:
            first_jalali = jdatetime.date(
                self.view_year,
                self.view_month,
                1,
            )

            first_gregorian = first_jalali.togregorian()

            if self.view_month == 12:
                next_jalali = jdatetime.date(
                    self.view_year + 1,
                    1,
                    1,
                )
            else:
                next_jalali = jdatetime.date(
                    self.view_year,
                    self.view_month + 1,
                    1,
                )

            day_count = (
                next_jalali.togregorian()
                - first_gregorian
            ).days

            leading = first_jalali.weekday()

        else:
            first_gregorian = date(
                self.view_year,
                self.view_month,
                1,
            )

            day_count = monthrange(
                self.view_year,
                self.view_month,
            )[1]

            leading = first_gregorian.weekday()

        return first_gregorian, day_count, leading

    def day_number(self, value):
        if is_rtl() and jdatetime is not None:
            return jdatetime.date.fromgregorian(
                date=value
            ).day

        return value.day

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        scroll_area.setWidget(content)

        root_layout.addWidget(scroll_area)

        layout = QVBoxLayout(content)

        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        add_button = PrimaryButton("＋ Add Event")

        add_button.clicked.connect(
            lambda: self.add_event()
        )

        header = PageHeader(
            "Calendar",
            (
                "Manage exams, classes, deadlines "
                "and important events."
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
            "🔍 Search events..."
        )

        self.search_input.textChanged.connect(
            self.refresh_calendar
        )

        self.course_filter = QComboBox()

        add_combo_item(
            self.course_filter,
            "All Courses",
            None,
        )

        self.course_filter.currentIndexChanged.connect(
            self.refresh_calendar
        )

        self.type_filter = QComboBox()

        add_combo_item(
            self.type_filter,
            "All Event Types",
            None,
        )

        add_combo_items(
            self.type_filter,
            EVENT_TYPES,
        )

        self.type_filter.currentIndexChanged.connect(
            self.refresh_calendar
        )

        today_button = SecondaryButton("Today")

        today_button.clicked.connect(
            self.go_to_today
        )

        refresh_button = SecondaryButton("↻ Refresh")

        refresh_button.clicked.connect(
            self.refresh_data
        )

        filters.addWidget(
            self.search_input,
            stretch=1,
        )
        filters.addWidget(self.course_filter)
        filters.addWidget(self.type_filter)
        filters.addWidget(today_button)
        filters.addWidget(refresh_button)

        layout.addLayout(filters)

        # ----------------------------------------------------
        # CALENDAR + DAY PANEL
        # ----------------------------------------------------

        body = QHBoxLayout()
        body.setSpacing(18)

        self.calendar_card = QFrame()

        self.calendar_card.setObjectName(
            "calendarCard"
        )

        calendar_layout = QVBoxLayout(
            self.calendar_card
        )

        calendar_layout.setContentsMargins(
            16,
            14,
            16,
            16,
        )

        calendar_layout.setSpacing(10)

        month_bar = QHBoxLayout()
        month_bar.setSpacing(6)

        previous_button = SecondaryButton("‹")

        previous_button.setObjectName("calendarNav")

        previous_button.setFixedWidth(44)

        previous_button.clicked.connect(
            self.go_previous_month
        )

        next_button = SecondaryButton("›")

        next_button.setObjectName("calendarNav")

        next_button.setFixedWidth(44)

        next_button.clicked.connect(
            self.go_next_month
        )

        self.month_label = QLabel()

        self.month_label.setObjectName(
            "calendarMonthTitle"
        )

        self.month_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        month_bar.addWidget(previous_button)
        month_bar.addWidget(
            self.month_label,
            stretch=1,
        )
        month_bar.addWidget(next_button)

        calendar_layout.addLayout(month_bar)

        self.grid_widget = QWidget()

        self.grid = QGridLayout(self.grid_widget)

        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(5)

        for column in range(7):
            self.grid.setColumnStretch(column, 1)

        calendar_layout.addWidget(
            self.grid_widget,
            stretch=1,
        )

        body.addWidget(
            self.calendar_card,
            stretch=3,
        )

        # -- Day panel --------------------------------------

        self.side_panel = QFrame()

        self.side_panel.setObjectName("contentCard")

        self.side_panel.setMinimumWidth(310)

        side_layout = QVBoxLayout(
            self.side_panel
        )

        side_layout.setContentsMargins(18, 16, 18, 16)
        side_layout.setSpacing(12)

        self.day_title = QLabel()

        self.day_title.setObjectName("sectionTitle")

        self.day_title.setWordWrap(True)

        self.add_day_button = PrimaryButton(
            "＋ Add Event"
        )

        self.add_day_button.clicked.connect(
            self.add_event_for_selected_day
        )

        self.events_scroll = QScrollArea()

        self.events_scroll.setWidgetResizable(True)

        self.events_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.events_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.events_scroll.setMinimumHeight(300)

        self.events_container = QWidget()

        self.events_layout = QVBoxLayout(
            self.events_container
        )

        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(10)

        self.events_scroll.setWidget(
            self.events_container
        )

        side_layout.addWidget(self.day_title)
        side_layout.addWidget(self.add_day_button)
        side_layout.addWidget(
            self.events_scroll,
            stretch=1,
        )

        body.addWidget(
            self.side_panel,
            stretch=2,
        )

        layout.addLayout(body)

        layout.addStretch()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_data(self):
        try:
            self.events = get_all_calendar_events()
            self.courses = get_all_courses()

        except Exception as error:
            show_error(
                self,
                "Unable to load calendar events",
                str(error),
            )
            return

        self.populate_course_filter()
        self.refresh_calendar()
        self.refresh_day_panel()

    def populate_course_filter(self):
        current_course = self.course_filter.currentData()

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

        for index in range(self.course_filter.count()):
            if (
                self.course_filter.itemData(index)
                == current_course
            ):
                self.course_filter.setCurrentIndex(index)
                break

        self.course_filter.blockSignals(False)

    def filtered_events(self):
        search_text = (
            self.search_input.text().strip().lower()
        )

        selected_course = self.course_filter.currentData()

        selected_type = self.type_filter.currentData()

        result = []

        for event in self.events:
            searchable = " ".join(
                [
                    event.title or "",
                    event.description or "",
                ]
            ).lower()

            if (
                search_text
                and search_text not in searchable
            ):
                continue

            if (
                selected_course is not None
                and event.course_id != selected_course
            ):
                continue

            if (
                selected_type is not None
                and event.event_type != selected_type
            ):
                continue

            result.append(event)

        return result

    # ========================================================
    # CALENDAR GRID
    # ========================================================

    def refresh_calendar(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.month_label.setText(
            month_title(
                self.view_year,
                self.view_month,
            )
        )

        headers = weekday_headers()

        for column, title in enumerate(headers):
            label = QLabel(title)

            label.setObjectName("weekdayHeader")

            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.grid.addWidget(label, 0, column)

        events_by_day = {}

        for event in self.filtered_events():
            event_day = event_date(event)

            if event_day is None:
                continue

            events_by_day.setdefault(
                event_day.isoformat(),
                [],
            ).append(event)

        first_date, day_count, leading = (
            self.month_context()
        )

        cell_count = (
            (leading + day_count + 6) // 7
        ) * 7

        today_value = date.today()

        for index in range(cell_count):
            offset = index - leading

            day_value = first_date + timedelta(
                days=offset
            )

            in_current_month = (
                0 <= offset < day_count
            )

            events = events_by_day.get(
                day_value.isoformat(),
                [],
            )

            cell = CalendarDay(
                day_date=day_value,
                day_number=self.day_number(day_value),
                in_current_month=in_current_month,
                selected=(day_value == self.selected_date),
                is_today=(day_value == today_value),
                events=events,
            )

            cell.clicked.connect(self.on_day_clicked)

            self.grid.addWidget(
                cell,
                index // 7 + 1,
                index % 7,
            )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def go_previous_month(self):
        year = self.view_year
        month = self.view_month - 1

        if month < 1:
            month = 12
            year -= 1

        self.view_year = year
        self.view_month = month
        self.selected_date = self.first_day_of_view()

        self.refresh_calendar()
        self.refresh_day_panel()

    def go_next_month(self):
        year = self.view_year
        month = self.view_month + 1

        if month > 12:
            month = 1
            year += 1

        self.view_year = year
        self.view_month = month
        self.selected_date = self.first_day_of_view()

        self.refresh_calendar()
        self.refresh_day_panel()

    def go_to_today(self):
        self.selected_date = date.today()

        self.set_view_to_date(self.selected_date)

        self.refresh_calendar()
        self.refresh_day_panel()

    def on_day_clicked(self, day_value):
        if not self.same_display_month(day_value):
            self.set_view_to_date(day_value)

        self.selected_date = day_value

        self.refresh_calendar()
        self.refresh_day_panel()

    # ========================================================
    # DAY PANEL
    # ========================================================

    def clear_day_events(self):
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def refresh_day_panel(self):
        self.day_title.setText(
            trf(
                "Events on {date}",
                date=format_date(
                    self.selected_date,
                    include_weekday=True,
                ),
            )
        )

        self.clear_day_events()

        day_events = [
            event
            for event in self.filtered_events()
            if event_date(event) == self.selected_date
        ]

        day_events.sort(
            key=lambda event: event.start_datetime or ""
        )

        if not day_events:
            title = QLabel(
                tr("No events on this day")
            )

            title.setObjectName("sectionTitle")

            message = QLabel(
                tr("Add an event for this date.")
            )

            message.setObjectName("subtitle")

            message.setWordWrap(True)

            self.events_layout.addWidget(title)
            self.events_layout.addWidget(message)
            self.events_layout.addStretch()

            return

        course_names = {
            course.id: course.name
            for course in self.courses
        }

        for event in day_events:
            self.events_layout.addWidget(
                self.create_event_row(
                    event,
                    course_names,
                )
            )

        self.events_layout.addStretch()

    def create_event_row(self, event, course_names):
        row = QFrame()

        row.setObjectName("eventRow")

        layout = QVBoxLayout(row)

        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(6)

        title = QLabel(event.title)

        title.setWordWrap(True)

        title.setStyleSheet(
            "font-weight: 700;"
        )

        top.addWidget(title, stretch=1)

        edit_button = SecondaryButton("✏ Edit")

        edit_button.clicked.connect(
            lambda _checked=False,
            current=event:
            self.edit_event(current)
        )

        delete_button = DangerButton("🗑 Delete")

        delete_button.clicked.connect(
            lambda _checked=False,
            current=event:
            self.delete_event(current)
        )

        top.addWidget(edit_button)
        top.addWidget(delete_button)

        layout.addLayout(top)

        details = []

        time_text = event_time(event)

        if time_text:
            details.append(
                f"🕒 {localize_digits(time_text)}"
            )

        details.append(tr(event.event_type))

        course_name = course_names.get(event.course_id)

        if course_name:
            details.append(f"📚 {course_name}")

        details_label = QLabel(
            "   •   ".join(details)
        )

        details_label.setObjectName("subtitle")

        details_label.setWordWrap(True)

        layout.addWidget(details_label)

        if event.description:
            description = QLabel(event.description)

            description.setObjectName("subtitle")

            description.setWordWrap(True)

            layout.addWidget(description)

        return row

    # ========================================================
    # ADD
    # ========================================================

    def add_event_for_selected_day(self):
        self.add_event(self.selected_date)

    def add_event(self, default_date=None):
        dialog = CalendarEventDialog(
            default_date=default_date,
            parent=self,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            create_calendar_event(
                title=data["title"],
                event_type=data["event_type"],
                start_datetime=data["start_datetime"],
                course_id=data["course_id"],
                end_datetime=data["end_datetime"],
                description=data["description"],
            )

        except Exception as error:
            show_error(
                self,
                "Unable to create event",
                str(error),
            )
            return

        self.refresh_data()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_event(self, event):
        dialog = CalendarEventDialog(
            event=event,
            parent=self,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        data = dialog.get_data()

        try:
            updated = update_calendar_event(
                event_id=event.id,
                title=data["title"],
                event_type=data["event_type"],
                start_datetime=data["start_datetime"],
                course_id=data["course_id"],
                end_datetime=data["end_datetime"],
                description=data["description"],
            )

            if not updated:
                show_error(
                    self,
                    "Update failed",
                    (
                        "The calendar event could not "
                        "be updated."
                    ),
                )
                return

        except Exception as error:
            show_error(
                self,
                "Unable to update event",
                str(error),
            )
            return

        self.refresh_data()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_event(self, event):
        confirmed = confirm_delete(
            self,
            "Delete Calendar Event",
            trf(
                'Are you sure you want to delete "{name}"?'
                "\n\nThis action cannot be undone.",
                name=event.title,
            ),
        )

        if not confirmed:
            return

        try:
            deleted = delete_calendar_event(event.id)

            if not deleted:
                show_error(
                    self,
                    "Delete failed",
                    (
                        "The calendar event could not "
                        "be deleted."
                    ),
                )
                return

        except Exception as error:
            show_error(
                self,
                "Unable to delete event",
                str(error),
            )
            return

        self.refresh_data()
