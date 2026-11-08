"""Arabic/Persian aware interface helpers for StudyFlow.

The project stores every date in the database as a Gregorian date.  This
module only changes how text and dates are *presented*; canonical values
(status names, dates, event types, ...) are never translated in the model.

The public API is intentionally small:

``tr(text)`` / ``trf(template, **values)``
    Translate static text / formatted templates.
``set_language`` / ``get_language`` / ``is_rtl``
    Switch and query the interface language.
``apply_translations(widget)``
    Walk a widget tree and retranslate all user-visible text.
``format_date`` / ``format_datetime`` / ``format_duration``
    Locale aware value formatting.
``localize_digits``
    Convert Latin digits to Persian digits when needed.
"""

from __future__ import annotations

from datetime import date, datetime

try:
    import jdatetime
except ImportError:  # pragma: no cover - GUI dependency is optional for tests
    jdatetime = None

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QComboBox,
    QDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)


# ============================================================
# LANGUAGES
# ============================================================

ENGLISH = "English"
PERSIAN = "Persian"

LANGUAGES = (
    ENGLISH,
    PERSIAN,
)

_current_language = ENGLISH


# Canonical values stored inside QComboBox items.  The display text can be
# translated without ever losing the English value used by the service layer.
COMBO_CANONICAL_ROLE = Qt.ItemDataRole.UserRole + 20


# ============================================================
# PERSIAN CALENDAR NAMES
# ============================================================

PERSIAN_MONTHS = (
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
)

# jdatetime uses Saturday = 0.
PERSIAN_WEEKDAYS = (
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
)

PERSIAN_WEEKDAY_HEADERS = (
    "ش",
    "ی",
    "د",
    "س",
    "چ",
    "پ",
    "ج",
)

ENGLISH_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

# Python's date.weekday() uses Monday = 0.
ENGLISH_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

ENGLISH_WEEKDAY_HEADERS = (
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
)


FA_DIGITS = str.maketrans(
    "0123456789",
    "۰۱۲۳۴۵۶۷۸۹",
)


# ============================================================
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {
    # --------------------------------------------------------
    # Navigation / common
    # --------------------------------------------------------
    "Dashboard": "داشبورد",
    "Courses": "دوره‌ها",
    "Assignments": "تکالیف",
    "Resources": "منابع",
    "Study Sessions": "جلسات مطالعه",
    "Calendar": "تقویم",
    "Settings": "تنظیمات",
    "Refresh": "بازخوانی",
    "↻ Refresh": "↻ بازخوانی",
    "Edit": "ویرایش",
    "✏ Edit": "✏ ویرایش",
    "Delete": "حذف",
    "🗑 Delete": "🗑 حذف",
    "Archive": "بایگانی",
    "📦 Archive": "📦 بایگانی",
    "Restore": "بازیابی",
    "♻ Restore": "♻ بازیابی",
    "Open Resource": "بازکردن منبع",
    "🌐 Open Resource": "🌐 بازکردن منبع",
    "Save": "ذخیره",
    "Cancel": "انصراف",
    "OK": "تأیید",
    "Yes": "بله",
    "No": "خیر",
    "Error": "خطا",
    "Information": "اطلاعات",
    "Warning": "هشدار",
    "Nothing here yet": "هنوز چیزی اینجا نیست",
    "There is nothing to display.": "چیزی برای نمایش وجود ندارد.",
    "Delete": "حذف",
    "Are you sure you want to delete this item?": (
        "آیا از حذف این مورد مطمئن هستید؟"
    ),
    "An unexpected error occurred.": "خطای غیرمنتظره‌ای رخ داد.",
    "Update failed": "به‌روزرسانی ناموفق",
    "Delete failed": "حذف ناموفق",
    "Unable to save settings": "ذخیره تنظیمات ناموفق بود",
    "Settings saved": "تنظیمات ذخیره شد",
    "General": "عمومی",
    "Unknown Course": "دوره ناشناخته",
    "No deadline": "بدون مهلت",
    "Notes": "یادداشت‌ها",
    "Status": "وضعیت",
    "Priority": "اولویت",
    "Progress": "پیشرفت",
    "Description": "توضیحات",
    "Title *": "عنوان *",
    "Course": "دوره",
    "Course *": "دوره *",
    "Type *": "نوع *",
    "Author": "نویسنده",
    "Category": "دسته‌بندی",
    "URL": "نشانی",
    "Start *": "شروع *",
    "End": "پایان",
    "Deadline": "مهلت",
    "Instructor": "استاد",
    "Credits": "واحد",
    "Semester": "ترم",
    "Color": "رنگ",

    # --------------------------------------------------------
    # Dialogs / validation
    # --------------------------------------------------------
    "Please enter a course name.": "لطفاً نام دوره را وارد کنید.",
    "Course name required": "نام دوره لازم است",
    "Course required": "دوره لازم است",
    "Title required": "عنوان لازم است",
    "Date required": "تاریخ لازم است",
    "Type required": "نوع لازم است",
    "Invalid duration": "مدت نامعتبر",
    "Start date required": "تاریخ شروع لازم است",
    "End date required": "تاریخ پایان لازم است",
    "Please enter a resource title.": "لطفاً عنوان منبع را وارد کنید.",
    "Please select a resource type.": "لطفاً نوع منبع را انتخاب کنید.",
    "Please enter an assignment title.": "لطفاً عنوان تکلیف را وارد کنید.",
    "Please create and select a course first.": (
        "ابتدا یک دوره ایجاد و انتخاب کنید."
    ),
    "Please select a course.": "لطفاً یک دوره انتخاب کنید.",
    "Please enter the study date.": "لطفاً تاریخ مطالعه را وارد کنید.",
    "Duration must be greater than zero.": "مدت باید بیشتر از صفر باشد.",
    "Please enter an event title.": "لطفاً عنوان رویداد را وارد کنید.",
    "Please enter the event start date and time.": (
        "لطفاً تاریخ و زمان شروع رویداد را وارد کنید."
    ),
    "Enter an end date and time or disable the end date.": (
        "تاریخ و زمان پایان را وارد کنید یا پایان را غیرفعال کنید."
    ),
    "No active courses": "دوره فعالی وجود ندارد",
    "Create an active course before adding an assignment.": (
        "پیش از افزودن تکلیف، یک دوره فعال بسازید."
    ),
    "Create an active course before logging a study session.": (
        "پیش از ثبت جلسه مطالعه، یک دوره فعال بسازید."
    ),
    "Unable to load courses": "بارگذاری دوره‌ها ناموفق بود",
    "Unable to create course": "ایجاد دوره ناموفق بود",
    "Unable to update course": "به‌روزرسانی دوره ناموفق بود",
    "Unable to delete course": "حذف دوره ناموفق بود",
    "Unable to load assignments": "بارگذاری تکالیف ناموفق بود",
    "Unable to create assignment": "ایجاد تکلیف ناموفق بود",
    "Unable to update assignment": "به‌روزرسانی تکلیف ناموفق بود",
    "Unable to update status": "به‌روزرسانی وضعیت ناموفق بود",
    "Unable to delete assignment": "حذف تکلیف ناموفق بود",
    "Unable to load resources": "بارگذاری منابع ناموفق بود",
    "Unable to create resource": "ایجاد منبع ناموفق بود",
    "Unable to update resource": "به‌روزرسانی منبع ناموفق بود",
    "Unable to delete resource": "حذف منبع ناموفق بود",
    "Unable to load study sessions": "بارگذاری جلسات مطالعه ناموفق بود",
    "Unable to create study session": "ایجاد جلسه مطالعه ناموفق بود",
    "Unable to update study session": "به‌روزرسانی جلسه مطالعه ناموفق بود",
    "Unable to delete study session": "حذف جلسه مطالعه ناموفق بود",
    "Unable to load calendar events": "بارگذاری رویدادهای تقویم ناموفق بود",
    "Unable to create event": "ایجاد رویداد ناموفق بود",
    "Unable to update event": "به‌روزرسانی رویداد ناموفق بود",
    "Unable to delete event": "حذف رویداد ناموفق بود",

    # --------------------------------------------------------
    # Statuses / priorities
    # --------------------------------------------------------
    "Not Started": "شروع نشده",
    "In Progress": "در حال انجام",
    "Completed": "انجام شده",
    "Low": "کم",
    "Medium": "متوسط",
    "High": "زیاد",

    # --------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------
    "Here's an overview of your study progress.": (
        "نمای کلی پیشرفت مطالعه شما."
    ),
    "Today's Tasks": "تکالیف امروز",
    "Upcoming Deadlines": "مهلت‌های نزدیک",
    "Active Courses": "دوره‌های فعال",
    "Overall Progress": "پیشرفت کلی",
    "No tasks for today": "کاری برای امروز نیست",
    "You're all caught up for today.": (
        "برای امروز همه کارها انجام شده است."
    ),
    "No upcoming deadlines": "مهلت نزدیکی وجود ندارد",
    "Add an assignment with a deadline.": (
        "یک تکلیف با مهلت اضافه کنید."
    ),
    "Good Morning": "صبح بخیر",
    "Good Afternoon": "بعدازظهر بخیر",
    "Good Evening": "شب بخیر",

    # --------------------------------------------------------
    # Courses
    # --------------------------------------------------------
    "Manage your courses and organize your semester.": (
        "دوره‌های خود را مدیریت و ترم را سازماندهی کنید."
    ),
    "＋ Add Course": "＋ افزودن دوره",
    "Add Course": "افزودن دوره",
    "Edit Course": "ویرایش دوره",
    "🔍 Search courses...": "🔍 جستجوی دوره‌ها...",
    "All Courses": "همه دوره‌ها",
    "Active": "فعال",
    "Archived": "بایگانی‌شده",
    "No courses found": "دوره‌ای یافت نشد",
    "Add your first course or change the current filters.": (
        "اولین دوره خود را اضافه کنید یا فیلترها را تغییر دهید."
    ),
    "Example: Operating Systems": "مثال: سیستم‌عامل‌ها",
    "Optional": "اختیاری",
    "Not specified": "نامشخص",
    "Example: Fall 2026": "مثال: پاییز ۱۴۰۵",
    "Choose Color": "انتخاب رنگ",
    "Choose Course Color": "انتخاب رنگ دوره",
    "Course name *": "نام دوره *",
    "No additional information": "اطلاعات بیشتری وجود ندارد",
    "Archive": "بایگانی",
    "Restore": "بازیابی",
    "Delete Course": "حذف دوره",
    "The course could not be updated.": "به‌روزرسانی دوره ممکن نشد.",
    "The course status could not be changed.": (
        "وضعیت دوره تغییر نکرد."
    ),
    "The course could not be deleted.": "حذف دوره ممکن نشد.",

    # --------------------------------------------------------
    # Assignments
    # --------------------------------------------------------
    "Track your tasks, deadlines and study progress.": (
        "کارها، مهلت‌ها و پیشرفت مطالعه خود را پیگیری کنید."
    ),
    "＋ Add Assignment": "＋ افزودن تکلیف",
    "Add Assignment": "افزودن تکلیف",
    "Edit Assignment": "ویرایش تکلیف",
    "🔍 Search assignments...": "🔍 جستجوی تکالیف...",
    "All Statuses": "همه وضعیت‌ها",
    "No assignments found": "تکلیفی یافت نشد",
    "Add a new assignment or change your filters.": (
        "تکلیف جدیدی اضافه کنید یا فیلترها را تغییر دهید."
    ),
    "Example: Database Project": "مثال: پروژه پایگاه داده",
    "Optional description...": "توضیحات اختیاری...",
    "YYYY-MM-DD or Jalali date": "YYYY-MM-DD یا تاریخ شمسی",
    "Delete Assignment": "حذف تکلیف",
    "The assignment could not be updated.": (
        "به‌روزرسانی تکلیف ممکن نشد."
    ),
    "The assignment could not be deleted.": "حذف تکلیف ممکن نشد.",

    # --------------------------------------------------------
    # Resources
    # --------------------------------------------------------
    "Organize your books, PDFs, links and study materials.": (
        "کتاب‌ها، PDFها، لینک‌ها و مواد مطالعه خود را سازماندهی کنید."
    ),
    "＋ Add Resource": "＋ افزودن منبع",
    "Add Resource": "افزودن منبع",
    "Edit Resource": "ویرایش منبع",
    "🔍 Search resources...": "🔍 جستجوی منابع...",
    "All Types": "همه انواع",
    "No resources found": "منبعی یافت نشد",
    "Add your first study resource or change the filters.": (
        "اولین منبع مطالعه خود را اضافه کنید یا فیلترها را تغییر دهید."
    ),
    "No Course": "بدون دوره",
    "Example: Operating Systems Book": "مثال: کتاب سیستم‌عامل",
    "Optional author name": "نام نویسنده (اختیاری)",
    "Example: Reference": "مثال: مرجع",
    "Optional notes...": "یادداشت‌های اختیاری...",
    "Book": "کتاب",
    "Article": "مقاله",
    "Video": "ویدیو",
    "Website": "وب‌سایت",
    "Other": "سایر",
    "Open Resource": "بازکردن منبع",
    "Delete Resource": "حذف منبع",
    "The resource could not be updated.": "به‌روزرسانی منبع ممکن نشد.",
    "The resource could not be deleted.": "حذف منبع ممکن نشد.",

    # --------------------------------------------------------
    # Study sessions
    # --------------------------------------------------------
    "Track your study time and review your learning activity.": (
        "زمان مطالعه خود را ثبت و فعالیت یادگیری را مرور کنید."
    ),
    "＋ Log Study Session": "＋ ثبت جلسه مطالعه",
    "Add Study Session": "افزودن جلسه مطالعه",
    "Edit Study Session": "ویرایش جلسه مطالعه",
    "🔍 Search study notes...": "🔍 جستجوی یادداشت‌های مطالعه...",
    "Filter by date...": "فیلتر بر اساس تاریخ...",
    "No study sessions found": "جلسه مطالعه‌ای یافت نشد",
    "Log your first study session or change the filters.": (
        "اولین جلسه مطالعه خود را ثبت کنید یا فیلترها را تغییر دهید."
    ),
    "What did you study? (Optional)": "چه چیزی مطالعه کردید؟ (اختیاری)",
    "Study Date *": "تاریخ مطالعه *",
    "Duration *": "مدت *",
    " minutes": " دقیقه",
    "%": "٪",
    "Study Notes": "یادداشت‌های مطالعه",
    "Delete Study Session": "حذف جلسه مطالعه",
    "The study session could not be updated.": (
        "به‌روزرسانی جلسه مطالعه ممکن نشد."
    ),
    "The study session could not be deleted.": (
        "حذف جلسه مطالعه ممکن نشد."
    ),

    # --------------------------------------------------------
    # Calendar
    # --------------------------------------------------------
    "Manage exams, classes, deadlines and important events.": (
        "امتحان‌ها، کلاس‌ها، مهلت‌ها و رویدادهای مهم را مدیریت کنید."
    ),
    "＋ Add Event": "＋ افزودن رویداد",
    "Add Event": "افزودن رویداد",
    "Edit Event": "ویرایش رویداد",
    "Add Calendar Event": "افزودن رویداد تقویم",
    "Edit Calendar Event": "ویرایش رویداد تقویم",
    "No Course / General Event": "بدون دوره / رویداد عمومی",
    "Example: Database Midterm Exam": "مثال: امتحان میان‌ترم پایگاه داده",
    "Set an end date and time": "تعیین تاریخ و زمان پایان",
    "Event Type *": "نوع رویداد *",
    "Class": "کلاس",
    "Exam": "امتحان",
    "Study": "مطالعه",
    "Meeting": "جلسه",
    "Personal": "شخصی",
    "All Event Types": "همه انواع رویداد",
    "🔍 Search events...": "🔍 جستجوی رویدادها...",
    "Previous Month": "ماه قبل",
    "Next Month": "ماه بعد",
    "Today": "امروز",
    "No events found": "رویدادی یافت نشد",
    "No events match your filters.": (
        "هیچ رویدادی با فیلترهای شما مطابقت ندارد."
    ),
    "No events on this day": "رویدادی در این روز نیست",
    "Add an event for this date.": "برای این تاریخ رویداد اضافه کنید.",
    "Add Event for This Day": "افزودن رویداد برای این روز",
    "Delete Calendar Event": "حذف رویداد تقویم",
    "The calendar event could not be updated.": (
        "به‌روزرسانی رویداد تقویم ممکن نشد."
    ),
    "The calendar event could not be deleted.": (
        "حذف رویداد تقویم ممکن نشد."
    ),

    # --------------------------------------------------------
    # Settings
    # --------------------------------------------------------
    "Customize StudyFlow to match your style.": (
        "StudyFlow را با سلیقه خود هماهنگ کنید."
    ),
    "🖥 Appearance": "🖥 ظاهر",
    "Choose how StudyFlow looks on your screen.": (
        "نحوه نمایش StudyFlow را روی صفحه انتخاب کنید."
    ),
    "Dark": "تیره",
    "Light": "روشن",
    "System": "سیستم",
    "AMOLED": "AMOLED",
    "🎨 Color Theme": "🎨 رنگ اصلی",
    "Choose your favorite StudyFlow color palette.": (
        "پالت رنگ دلخواه StudyFlow را انتخاب کنید."
    ),
    "🌐 Language": "🌐 زبان",
    "Select the interface language.": "زبان رابط کاربری را انتخاب کنید.",
    "English": "انگلیسی",
    "Persian": "فارسی",
    "Blue + Green": "آبی + سبز",
    "Purple + Pink": "بنفش + صورتی",
    "Yellow + Orange": "زرد + نارنجی",
    "ℹ StudyFlow": "ℹ StudyFlow",
    "Version 1.0": "نسخه ۱.۰",
    "A personal academic management application for organizing courses, "
    "assignments and study sessions.": (
        "یک برنامه مدیریت تحصیلی شخصی برای سازمان‌دهی دوره‌ها، تکالیف و "
        "جلسات مطالعه."
    ),
    "↺ Reset": "↺ بازنشانی",
    "💾 Save Settings": "💾 ذخیره تنظیمات",

    # --------------------------------------------------------
    # Dynamic templates
    # --------------------------------------------------------
    "Deadline: {deadline}   •   Priority: {priority}": (
        "مهلت: {deadline}   •   اولویت: {priority}"
    ),
    "{course}   •   {deadline}": "{course}   •   {deadline}",
    "📅 Deadline: {deadline}": "📅 مهلت: {deadline}",
    "🔥 {priority}": "🔥 {priority}",
    "Progress: {progress}%": "پیشرفت: {progress}٪",
    "🎓 {count} credits": "🎓 {count} واحد",
    "📊 {count} sessions   •   ⏱ {duration} studied": (
        "📊 {count} جلسه   •   ⏱ {duration} مطالعه"
    ),
    "Events on {date}": "رویدادهای {date}",
    "+{count} more": "+{count} مورد دیگر",
    'Are you sure you want to delete "{name}"?\n\n'
    "This action cannot be undone.": (
        'آیا از حذف "{name}" مطمئن هستید؟\n\n'
        "این عمل قابل بازگشت نیست."
    ),
    'Delete the study session for "{date}"?\n\n'
    "This action cannot be undone.": (
        'جلسه مطالعه "{date}" حذف شود؟\n\n'
        "این عمل قابل بازگشت نیست."
    ),
}


# ============================================================
# LANGUAGE STATE
# ============================================================

def get_language():
    """Return the active interface language."""
    return _current_language


def set_language(language):
    """Set the active interface language."""
    global _current_language

    if language not in LANGUAGES:
        language = ENGLISH

    _current_language = language


def is_rtl():
    """Return True when the active language uses a right-to-left layout."""
    return _current_language == PERSIAN


def tr(text):
    """Translate a static English string."""
    if text is None:
        return ""

    if _current_language == ENGLISH:
        return text

    return TRANSLATIONS.get(text, text)


def trf(template, **values):
    """Translate a template and substitute its named placeholders."""
    translated = tr(template)

    try:
        return translated.format(**values)
    except (KeyError, IndexError, ValueError):
        return translated


def total_translations():
    """Small helper used by tests and diagnostics."""
    return len(TRANSLATIONS)


# ============================================================
# DIGITS / DATE FORMATTING
# ============================================================

def to_persian_digits(value):
    """Convert Latin digits in *value* to Persian digits."""
    return str(value).translate(FA_DIGITS)


def localize_digits(value):
    """Convert digits to Persian when the active language is Persian."""
    if _current_language == PERSIAN:
        return to_persian_digits(value)

    return str(value)


def _coerce_date(value):
    """Return a Gregorian ``datetime.date`` for a stored/displayed value."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    # Date/time strings are stored as "YYYY-MM-DD HH:MM".
    date_part = text.split(" ")[0].split("T")[0]

    try:
        year, month, day = map(int, date_part.replace("/", "-").split("-"))
    except (TypeError, ValueError):
        return None

    # The project accepts Jalali dates in the 1000-1799 range and stores
    # them as Gregorian dates.
    if 1000 <= year < 1800:
        if jdatetime is None:
            return None

        try:
            return jdatetime.date(year, month, day).togregorian()
        except ValueError:
            return None

    try:
        return date(year, month, day)
    except ValueError:
        return None


def format_date(value, include_weekday=False):
    """Format a stored date according to the active language."""
    parsed = _coerce_date(value)

    if parsed is None:
        return str(value) if value is not None else ""

    if _current_language == PERSIAN:
        if jdatetime is None:
            return localize_digits(parsed.isoformat())

        jalali = jdatetime.date.fromgregorian(date=parsed)
        month_name = PERSIAN_MONTHS[jalali.month - 1]
        weekday = PERSIAN_WEEKDAYS[jalali.weekday()]

        if include_weekday:
            text = f"{weekday} {jalali.day} {month_name} {jalali.year}"
        else:
            text = f"{jalali.day} {month_name} {jalali.year}"

        return localize_digits(text)

    month_name = ENGLISH_MONTHS[parsed.month - 1]
    weekday = ENGLISH_WEEKDAYS[parsed.weekday()]

    if include_weekday:
        return f"{weekday}, {month_name} {parsed.day}, {parsed.year}"

    return f"{month_name} {parsed.day}, {parsed.year}"


def format_datetime(value, include_weekday=False):
    """Format a stored ``YYYY-MM-DD HH:MM`` value."""
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    parts = text.split()
    date_text = parts[0]
    time_text = parts[1] if len(parts) > 1 else ""

    formatted_date = format_date(
        date_text,
        include_weekday=include_weekday,
    )

    if time_text:
        return f"{formatted_date} • {localize_digits(time_text)}"

    return formatted_date


def format_duration(minutes):
    """Format a duration in minutes using the active language."""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = 0

    if minutes < 0:
        minutes = 0

    if _current_language == PERSIAN:
        hours, remainder = divmod(minutes, 60)

        if hours and remainder:
            return (
                f"{localize_digits(hours)} ساعت و "
                f"{localize_digits(remainder)} دقیقه"
            )

        if hours:
            return f"{localize_digits(hours)} ساعت"

        return f"{localize_digits(minutes)} دقیقه"

    hours, remainder = divmod(minutes, 60)

    if hours and remainder:
        return f"{hours}h {remainder}m"

    if hours:
        return f"{hours}h"

    return f"{minutes} min"


def month_title(year, month):
    """Return a localized month/year title for the calendar."""
    if _current_language == PERSIAN:
        return localize_digits(
            f"{PERSIAN_MONTHS[month - 1]} {year}"
        )

    return f"{ENGLISH_MONTHS[month - 1]} {year}"


def weekday_headers():
    """Return the weekday header labels for the active calendar."""
    if _current_language == PERSIAN:
        return list(PERSIAN_WEEKDAY_HEADERS)

    return list(ENGLISH_WEEKDAY_HEADERS)


# ============================================================
# COMBO BOX HELPERS
# ============================================================

def add_combo_item(combo, text, data=None):
    """Add a combo item while keeping its canonical English value."""
    combo.addItem(tr(text), data)

    index = combo.count() - 1
    combo.setItemData(index, text, COMBO_CANONICAL_ROLE)

    return index


def add_combo_items(combo, values):
    """Add several canonical values to a combo box."""
    for value in values:
        add_combo_item(combo, value, value)


def select_combo_data(combo, canonical_value):
    """Select the item whose canonical/user data matches *canonical_value*."""
    for index in range(combo.count()):
        if combo.itemData(index) == canonical_value:
            combo.setCurrentIndex(index)
            return True

    return False


def translate_combo_items(combo):
    """Retranslate the display text of every canonical combo item."""
    combo.blockSignals(True)

    try:
        for index in range(combo.count()):
            canonical = combo.itemData(
                index,
                COMBO_CANONICAL_ROLE,
            )

            if canonical is None:
                data = combo.itemData(index)

                if isinstance(data, str):
                    canonical = data
                else:
                    continue

            display = tr(canonical)

            if combo.itemText(index) != display:
                combo.setItemText(index, display)
    finally:
        combo.blockSignals(False)


# ============================================================
# WIDGET TREE TRANSLATION
# ============================================================

def _apply_text(widget, getter, setter, key):
    """Translate one text property without destroying dynamic updates."""
    source_property = f"i18n_{key}_source"
    last_property = f"i18n_{key}_last"

    current = getter()

    if current is None:
        current = ""

    source = widget.property(source_property)
    last = widget.property(last_property)

    # A text that is neither the original source nor our previous output
    # was updated by application code.  Treat it as the new source.
    if source is None or (
        last is not None
        and current != last
        and current != source
    ):
        source = current
        widget.setProperty(source_property, source)

    translated = tr(source)

    if current != translated:
        setter(translated)

    widget.setProperty(last_property, translated)


def _translate_widget(widget):
    if widget.property("i18n_skip"):
        return

    if isinstance(widget, QComboBox):
        translate_combo_items(widget)
        return

    if isinstance(widget, QLabel):
        _apply_text(
            widget,
            widget.text,
            widget.setText,
            "label",
        )
        return

    if isinstance(widget, QAbstractButton):
        _apply_text(
            widget,
            widget.text,
            widget.setText,
            "button",
        )
        return

    if isinstance(widget, QGroupBox):
        _apply_text(
            widget,
            widget.title,
            widget.setTitle,
            "group",
        )
        return

    if isinstance(widget, QDialog):
        _apply_text(
            widget,
            widget.windowTitle,
            widget.setWindowTitle,
            "window",
        )
        # A dialog is also a widget, but it has no additional text.
        return

    if isinstance(widget, QLineEdit):
        _apply_text(
            widget,
            widget.placeholderText,
            widget.setPlaceholderText,
            "placeholder",
        )
        return

    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        _apply_text(
            widget,
            widget.placeholderText,
            widget.setPlaceholderText,
            "placeholder",
        )


def apply_translations(root):
    """Retranslate *root* and every child widget in its tree."""
    if root is None:
        return

    if isinstance(root, QWidget):
        _translate_widget(root)

        for widget in root.findChildren(QWidget):
            _translate_widget(widget)


def apply_layout_direction(widget):
    """Apply the current layout direction to one widget."""
    if widget is None:
        return

    widget.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft
        if is_rtl()
        else Qt.LayoutDirection.LeftToRight
    )


# ============================================================
# AUTOMATIC DIALOG TRANSLATION
# ============================================================

class _TranslationEventFilter(QObject):
    """Translate dialogs automatically when they are shown."""

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.Show
            and isinstance(watched, QWidget)
        ):
            apply_layout_direction(watched)
            apply_translations(watched)

        return False


_filter = None


def install_translator(application=None):
    """Install the automatic dialog translator once."""
    global _filter

    if application is None:
        application = QApplication.instance()

    if application is None:
        return None

    if _filter is None:
        _filter = _TranslationEventFilter(application)
        application.installEventFilter(_filter)

    return _filter
