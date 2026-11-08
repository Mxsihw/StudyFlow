from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


# ============================================================
# ACCENT COLOR THEMES
# ============================================================

COLOR_SCHEMES = {
    "Blue + Green": {
        "primary": "#3B82F6",
        "primary_hover": "#2563EB",
        "secondary": "#10B981",
        "secondary_hover": "#059669",
        "accent_soft": "rgba(59, 130, 246, 0.18)",
        "gradient": (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #3B82F6, "
            "stop:1 #10B981)"
        ),
    },

    "Purple + Pink": {
        "primary": "#8B5CF6",
        "primary_hover": "#7C3AED",
        "secondary": "#EC4899",
        "secondary_hover": "#DB2777",
        "accent_soft": "rgba(139, 92, 246, 0.18)",
        "gradient": (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #8B5CF6, "
            "stop:1 #EC4899)"
        ),
    },

    "Yellow + Orange": {
        "primary": "#EAB308",
        "primary_hover": "#CA8A04",
        "secondary": "#F97316",
        "secondary_hover": "#EA580C",
        "accent_soft": "rgba(234, 179, 8, 0.18)",
        "gradient": (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #EAB308, "
            "stop:1 #F97316)"
        ),
    },
}


# ============================================================
# ENVIRONMENT / APPEARANCE THEMES
# ============================================================

THEME_COLORS = {

    "Dark": {
        "window": "#171719",
        "sidebar": "#101012",

        "background": "#1B1B1E",
        "surface": "#232326",
        "surface_hover": "#2B2B30",

        "input": "#202024",
        "border": "#35353B",

        "text": "#F4F4F5",
        "text_secondary": "#A1A1AA",

        "danger": "#EF4444",
        "danger_hover": "#DC2626",

        "scrollbar": "#3F3F46",
    },

    "Light": {
        "window": "#F5F6FA",
        "sidebar": "#FFFFFF",

        "background": "#F5F6FA",
        "surface": "#FFFFFF",
        "surface_hover": "#F0F1F5",

        "input": "#FFFFFF",
        "border": "#E1E3EA",

        "text": "#18181B",
        "text_secondary": "#71717A",

        "danger": "#DC2626",
        "danger_hover": "#B91C1C",

        "scrollbar": "#C5C7CF",
    },

    "AMOLED": {
        "window": "#000000",
        "sidebar": "#000000",

        "background": "#000000",
        "surface": "#0A0A0A",
        "surface_hover": "#151515",

        "input": "#080808",
        "border": "#282828",

        "text": "#FFFFFF",
        "text_secondary": "#A1A1AA",

        "danger": "#EF4444",
        "danger_hover": "#DC2626",

        "scrollbar": "#303030",
    },
}


# ============================================================
# SYSTEM THEME
# ============================================================

def get_system_theme():

    color_scheme = (
        QGuiApplication.styleHints().colorScheme()
    )

    if color_scheme == Qt.ColorScheme.Dark:
        return "Dark"

    return "Light"


# ============================================================
# ACTIVE APPEARANCE
# ============================================================

def get_active_theme(appearance):

    if appearance == "System":
        return get_system_theme()

    if appearance in THEME_COLORS:
        return appearance

    return "Dark"


# ============================================================
# BUILD STYLESHEET
# ============================================================

def build_stylesheet(
    appearance="Dark",
    color_scheme="Purple + Pink",
    rtl=False,
):

    active_theme = get_active_theme(
        appearance
    )

    colors = THEME_COLORS[
        active_theme
    ]

    accent = COLOR_SCHEMES.get(
        color_scheme,
        COLOR_SCHEMES["Purple + Pink"],
    )

    primary = accent["primary"]
    primary_hover = accent["primary_hover"]

    secondary = accent["secondary"]
    secondary_hover = accent["secondary_hover"]

    accent_soft = accent["accent_soft"]
    gradient = accent["gradient"]

    sidebar_border_side = "left" if rtl else "right"
    sidebar_text_align = "right" if rtl else "left"

    return f"""

    /* ===================================================== */
    /* GLOBAL ENVIRONMENT */
    /* ===================================================== */

    QWidget {{
        color: {colors["text"]};
        font-family: "Segoe UI";
        font-size: 14px;
    }}

    QMainWindow {{
        background-color: {colors["window"]};
    }}

    QWidget#centralWidget {{
        background-color: {colors["background"]};
    }}

    QStackedWidget {{
        background-color: {colors["background"]};
    }}

    /* ===================================================== */
    /* SIDEBAR */
    /* ===================================================== */

    QWidget#sidebar {{
        background-color: {colors["sidebar"]};
        border-{sidebar_border_side}: 1px solid {colors["border"]};
    }}

    QLabel#appLogo {{
        color: {primary};
        font-size: 22px;
        font-weight: 900;
    }}

    QLabel#appName {{
        color: {colors["text"]};
        font-size: 19px;
        font-weight: 800;
    }}

    QPushButton#sidebarButton {{
        background-color: transparent;
        color: {colors["text_secondary"]};

        border: none;
        border-radius: 10px;

        padding: 11px 14px;

        text-align: {sidebar_text_align};
        font-size: 14px;
        font-weight: 600;
    }}

    QPushButton#sidebarButton:hover {{
        background-color: {colors["surface_hover"]};
        color: {colors["text"]};
    }}

    /* ACTIVE SIDEBAR ITEM = ACCENT */
    QPushButton#sidebarButton:checked {{
        background: {gradient};
        color: white;
        font-weight: 800;
    }}

    QPushButton#collapseButton {{
        background-color: transparent;
        color: {colors["text_secondary"]};

        border: none;
        border-radius: 10px;

        padding: 8px;
        font-size: 20px;
    }}

    QPushButton#collapseButton:hover {{
        background-color: {colors["surface_hover"]};
        color: {primary};
    }}

    /* ===================================================== */
    /* PAGE BACKGROUND */
    /* ===================================================== */

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: {colors["background"]};
    }}

    /* ===================================================== */
    /* PAGE HEADERS */
    /* ===================================================== */

    QLabel#pageTitle {{
        color: {colors["text"]};
        font-size: 30px;
        font-weight: 900;
    }}

    QLabel#pageSubtitle,
    QLabel#subtitle {{
        color: {colors["text_secondary"]};
        font-size: 14px;
    }}

    /* ===================================================== */
    /* NORMAL CARDS */
    /* ===================================================== */

    QFrame#dataCard {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
    }}

    QFrame#dataCard:hover {{
        border-color: {primary};
    }}

    /* ===================================================== */
    /* IMPORTANT / STAT CARDS */
    /* ===================================================== */

    QFrame#statCard {{
        background-color: {colors["surface"]};
        border: 1px solid {primary};
        border-radius: 16px;
    }}

    QFrame#statCard:hover {{
        border: 2px solid {secondary};
    }}

    QLabel#statValue {{
        color: {primary};
        font-size: 30px;
        font-weight: 800;
    }}

    QLabel#cardLabel {{
        color: {colors["text_secondary"]};
        font-size: 13px;
        font-weight: 600;
    }}

    QLabel#cardIcon {{
        font-size: 24px;
    }}

    /* Dashboard content panels */
    QFrame#contentCard {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
    }}

    QLabel#sectionTitle {{
        color: {colors["text"]};
        font-size: 17px;
        font-weight: 800;
    }}

    /* Optional accent card */
    QFrame#accentCard {{
        background: {gradient};
        border: none;
        border-radius: 16px;
        color: white;
    }}

    /* ===================================================== */
    /* BUTTONS */
    /* ===================================================== */

    QPushButton {{
        background-color: {colors["surface_hover"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};
        border-radius: 9px;

        padding: 9px 16px;
        font-weight: 700;
    }}

    QPushButton:hover {{
        border-color: {primary};
    }}

    QPushButton:disabled {{
        color: {colors["text_secondary"]};
        background-color: {colors["surface"]};
    }}

    QDialogButtonBox QPushButton {{
        min-width: 88px;
    }}

    /* PRIMARY = ACCENT */
    QPushButton#primaryButton {{
        background: {gradient};
        color: white;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {primary_hover};
    }}

    QPushButton#primaryButton:pressed {{
        background-color: {secondary};
    }}

    /* SECONDARY = ENVIRONMENT */
    QPushButton#secondaryButton {{
        background-color: {colors["surface_hover"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};
    }}

    QPushButton#secondaryButton:hover {{
        border-color: {primary};
        background-color: {accent_soft};
    }}

    /* DANGER */
    QPushButton#dangerButton {{
        background-color: transparent;
        color: {colors["danger"]};

        border: 1px solid {colors["danger"]};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {colors["danger"]};
        color: white;
    }}

    /* ===================================================== */
    /* INPUTS */
    /* ===================================================== */

    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDateEdit,
    QDateTimeEdit {{
        background-color: {colors["input"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};
        border-radius: 9px;

        padding: 9px 11px;

        selection-background-color: {primary};
    }}

    QLineEdit:focus,
    QTextEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDateEdit:focus,
    QDateTimeEdit:focus {{
        border: 2px solid {primary};
    }}

    /* ===================================================== */
    /* COMBOBOX */
    /* ===================================================== */

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {colors["surface"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};

        selection-background-color: {primary};
        selection-color: white;

        outline: none;
    }}

    /* ===================================================== */
    /* CHECKBOX */
    /* ===================================================== */

    QCheckBox,
    QRadioButton {{
        color: {colors["text"]};
        spacing: 8px;
    }}

    QCheckBox::indicator,
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
    }}

    QCheckBox::indicator:unchecked {{
        border: 1px solid {colors["border"]};
        border-radius: 4px;
        background-color: {colors["input"]};
    }}

    QCheckBox::indicator:checked {{
        background-color: {primary};
        border: 1px solid {primary};
        border-radius: 4px;
    }}

    QRadioButton::indicator:unchecked {{
        border: 1px solid {colors["border"]};
        border-radius: 9px;
        background-color: {colors["input"]};
    }}

    QRadioButton::indicator:checked {{
        background-color: {primary};
        border: 5px solid {colors["input"]};
        border-radius: 9px;
    }}

    /* ===================================================== */
    /* TABLE */
    /* ===================================================== */

    QTableWidget {{
        background-color: {colors["surface"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};
        border-radius: 10px;

        gridline-color: {colors["border"]};
    }}

    QHeaderView::section {{
        background-color: {colors["surface_hover"]};
        color: {colors["text"]};

        border: none;
        border-bottom: 1px solid {colors["border"]};

        padding: 10px;
        font-weight: 700;
    }}

    QTableWidget::item:selected {{
        background-color: {accent_soft};
        color: {colors["text"]};
    }}

    /* ===================================================== */
    /* SCROLLBAR */
    /* ===================================================== */

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors["scrollbar"]};
        border-radius: 5px;
        min-height: 35px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {primary};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ===================================================== */
    /* PROGRESS BAR */
    /* ===================================================== */

    QProgressBar {{
        background-color: {colors["surface_hover"]};
        border: none;
        border-radius: 7px;

        text-align: center;
        color: {colors["text"]};
    }}

    QProgressBar::chunk {{
        background: {gradient};
        border-radius: 7px;
    }}

    /* ===================================================== */
    /* CALENDAR */
    /* ===================================================== */

    QCalendarWidget {{
        background-color: {colors["surface"]};
        color: {colors["text"]};
    }}

    QCalendarWidget QWidget {{
        background-color: {colors["surface"]};
        color: {colors["text"]};
    }}

    QCalendarWidget QToolButton {{
        background-color: transparent;
        color: {colors["text"]};
        border-radius: 8px;
        padding: 6px;
    }}

    QCalendarWidget QToolButton:hover {{
        background-color: {accent_soft};
        color: {primary};
    }}

    QCalendarWidget QAbstractItemView {{
        selection-background-color: {primary};
        selection-color: white;

        background-color: {colors["surface"]};
        color: {colors["text"]};
    }}

    /* ===================================================== */
    /* CUSTOM MONTHLY CALENDAR */
    /* ===================================================== */

    QFrame#calendarCard {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
    }}

    QLabel#calendarMonthTitle {{
        color: {colors["text"]};
        font-size: 20px;
        font-weight: 800;
    }}

    QLabel#weekdayHeader {{
        color: {colors["text_secondary"]};
        font-size: 12px;
        font-weight: 700;
        padding: 4px;
    }}

    QPushButton#calendarNav {{
        background-color: transparent;
        color: {colors["text"]};
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 4px 12px;
        font-size: 19px;
        font-weight: 800;
        min-width: 34px;
    }}

    QPushButton#calendarNav:hover {{
        background-color: {accent_soft};
        border-color: {primary};
        color: {primary};
    }}

    QFrame#calendarDay {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
    }}

    QFrame#calendarDay:hover {{
        background-color: {colors["surface_hover"]};
        border-color: {colors["border"]};
    }}

    QFrame#calendarDay[selected="true"] {{
        background-color: {accent_soft};
        border: 2px solid {primary};
    }}

    QFrame#calendarDay[today="true"] {{
        border: 1px solid {secondary};
    }}

    QLabel#dayNumber {{
        color: {colors["text"]};
        font-size: 13px;
        font-weight: 700;
    }}

    QLabel#dayNumber[muted="true"] {{
        color: {colors["text_secondary"]};
    }}

    QLabel#eventChip {{
        background-color: {accent_soft};
        color: {primary};
        border-radius: 5px;
        padding: 1px 5px;
        font-size: 10px;
        font-weight: 600;
    }}

    QLabel#eventChipMore {{
        color: {colors["text_secondary"]};
        font-size: 10px;
    }}

    QFrame#eventRow {{
        background-color: {colors["surface_hover"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
    }}

    /* ===================================================== */
    /* DIALOGS */
    /* ===================================================== */

    QDialog {{
        background-color: {colors["window"]};
        color: {colors["text"]};
    }}

    QMessageBox {{
        background-color: {colors["window"]};
    }}

    /* ===================================================== */
    /* TOOLTIP */
    /* ===================================================== */

    QToolTip {{
        background-color: {colors["surface"]};
        color: {colors["text"]};

        border: 1px solid {colors["border"]};

        padding: 6px;
    }}
    """


# ============================================================
# APPLY THEME
# ============================================================

def apply_theme(
    application,
    appearance="Dark",
    color_scheme="Purple + Pink",
    rtl=False,
):

    stylesheet = build_stylesheet(
        appearance=appearance,
        color_scheme=color_scheme,
        rtl=rtl,
    )

    application.setStyleSheet(
        stylesheet
    )


# ============================================================
# GET COLORS
# ============================================================

def get_theme_colors(
    appearance="Dark",
    color_scheme="Purple + Pink",
):

    active_theme = get_active_theme(
        appearance
    )

    colors = THEME_COLORS[
        active_theme
    ].copy()

    colors.update(
        COLOR_SCHEMES.get(
            color_scheme,
            COLOR_SCHEMES["Purple + Pink"],
        )
    )

    return colors