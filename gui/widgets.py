from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import tr
# ============================================================
# SCROLLABLE PAGE
# ============================================================

class ScrollablePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.content = QWidget()

        self.content_layout = QVBoxLayout(
            self.content
        )

        self.content_layout.setContentsMargins(
            36,
            30,
            36,
            30,
        )

        self.content_layout.setSpacing(
            20
        )

        self.scroll_area.setWidget(
            self.content
        )

        root_layout.addWidget(
            self.scroll_area
        )
# ============================================================
# PRIMARY BUTTON
# ============================================================

class PrimaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self.setObjectName("primaryButton")

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(40)


# ============================================================
# SECONDARY BUTTON
# ============================================================

class SecondaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self.setObjectName("secondaryButton")

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(40)


# ============================================================
# DANGER BUTTON
# ============================================================

class DangerButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self.setObjectName("dangerButton")

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(40)


# ============================================================
# PAGE HEADER
# ============================================================

class PageHeader(QWidget):
    def __init__(
        self,
        title,
        subtitle="",
        action_widget=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setup_ui(
            title,
            subtitle,
            action_widget,
        )

    def setup_ui(
        self,
        title,
        subtitle,
        action_widget,
    ):
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(16)

        # ----------------------------------------------------
        # TEXT SECTION
        # ----------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        text_layout.setSpacing(4)

        title_label = QLabel(title)

        title_label.setObjectName(
            "pageTitle"
        )

        text_layout.addWidget(
            title_label
        )

        if subtitle:
            subtitle_label = QLabel(
                subtitle
            )

            subtitle_label.setObjectName(
                "pageSubtitle"
            )

            subtitle_label.setWordWrap(
                True
            )

            text_layout.addWidget(
                subtitle_label
            )

        layout.addLayout(
            text_layout,
            stretch=1,
        )

        # ----------------------------------------------------
        # ACTION
        # ----------------------------------------------------

        if action_widget is not None:
            action_widget.setSizePolicy(
                QSizePolicy.Policy.Maximum,
                QSizePolicy.Policy.Fixed,
            )

            layout.addWidget(
                action_widget,
                alignment=Qt.AlignmentFlag.AlignTop,
            )


# ============================================================
# EMPTY STATE
# ============================================================

class EmptyState(QFrame):
    def __init__(
        self,
        icon="📭",
        title="Nothing here yet",
        message="There is nothing to display.",
        action_widget=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "dataCard"
        )

        self.setup_ui(
            icon,
            title,
            message,
            action_widget,
        )

    def setup_ui(
        self,
        icon,
        title,
        message,
        action_widget,
    ):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        layout.setSpacing(10)

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ----------------------------------------------------
        # ICON
        # ----------------------------------------------------

        icon_label = QLabel(icon)

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setStyleSheet(
            """
            font-size: 48px;
            """
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_label = QLabel(title)

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            """
        )

        # ----------------------------------------------------
        # MESSAGE
        # ----------------------------------------------------

        message_label = QLabel(message)

        message_label.setObjectName(
            "subtitle"
        )

        message_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        message_label.setWordWrap(
            True
        )

        # ----------------------------------------------------
        # ADD
        # ----------------------------------------------------

        layout.addWidget(
            icon_label
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            message_label
        )

        if action_widget is not None:
            layout.addSpacing(10)

            layout.addWidget(
                action_widget,
                alignment=Qt.AlignmentFlag.AlignCenter,
            )


# ============================================================
# STAT CARD
# ============================================================

class StatCard(QFrame):
    def __init__(
        self,
        title,
        value,
        icon="📊",
        description="",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "statCard"
        )

        self.setup_ui(
            title,
            value,
            icon,
            description,
        )

    def setup_ui(
        self,
        title,
        value,
        icon,
        description,
    ):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(8)

        # ----------------------------------------------------
        # TOP ROW
        # ----------------------------------------------------

        top_row = QHBoxLayout()

        title_label = QLabel(title)

        title_label.setObjectName(
            "subtitle"
        )

        icon_label = QLabel(icon)

        icon_label.setStyleSheet(
            """
            font-size: 22px;
            """
        )

        top_row.addWidget(
            title_label,
            stretch=1,
        )

        top_row.addWidget(
            icon_label
        )

        # ----------------------------------------------------
        # VALUE
        # ----------------------------------------------------

        value_label = QLabel(
            str(value)
        )

        value_label.setStyleSheet(
            """
            font-size: 30px;
            font-weight: 800;
            """
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description_label = None

        if description:
            description_label = QLabel(
                description
            )

            description_label.setObjectName(
                "subtitle"
            )

            description_label.setWordWrap(
                True
            )

        # ----------------------------------------------------
        # ADD
        # ----------------------------------------------------

        layout.addLayout(
            top_row
        )

        layout.addWidget(
            value_label
        )

        if description_label is not None:
            layout.addWidget(
                description_label
            )


# ============================================================
# SECTION CARD
# ============================================================

class SectionCard(QFrame):
    def __init__(
        self,
        title=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "dataCard"
        )

        self.main_layout = QVBoxLayout(
            self
        )

        self.main_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        self.main_layout.setSpacing(12)

        if title:
            title_label = QLabel(title)

            title_label.setStyleSheet(
                """
                font-size: 17px;
                font-weight: 700;
                """
            )

            self.main_layout.addWidget(
                title_label
            )

    def add_widget(self, widget):
        self.main_layout.addWidget(
            widget
        )

    def add_layout(self, layout):
        self.main_layout.addLayout(
            layout
        )


# ============================================================
# CONFIRM DELETE
# ============================================================

def confirm_delete(
    parent,
    title="Delete",
    message=(
        "Are you sure you want to delete "
        "this item?"
    ),
):
    message_box = QMessageBox(parent)

    message_box.setIcon(
        QMessageBox.Icon.Warning
    )

    message_box.setWindowTitle(tr(title))

    message_box.setText(tr(message))

    yes_button = message_box.addButton(
        tr("Yes"),
        QMessageBox.ButtonRole.AcceptRole,
    )

    no_button = message_box.addButton(
        tr("No"),
        QMessageBox.ButtonRole.RejectRole,
    )

    message_box.setDefaultButton(no_button)

    message_box.exec()

    return message_box.clickedButton() is yes_button


# ============================================================
# SHOW ERROR
# ============================================================

def show_error(
    parent,
    title="Error",
    message="An unexpected error occurred.",
):
    message_box = QMessageBox(parent)

    message_box.setIcon(
        QMessageBox.Icon.Critical
    )

    message_box.setWindowTitle(tr(title))

    message_box.setText(tr(message))

    message_box.addButton(
        tr("OK"),
        QMessageBox.ButtonRole.AcceptRole,
    )

    message_box.exec()


# ============================================================
# SHOW INFO
# ============================================================

def show_info(
    parent,
    title="Information",
    message="",
):
    message_box = QMessageBox(parent)

    message_box.setIcon(
        QMessageBox.Icon.Information
    )

    message_box.setWindowTitle(tr(title))

    message_box.setText(tr(message))

    message_box.addButton(
        tr("OK"),
        QMessageBox.ButtonRole.AcceptRole,
    )

    message_box.exec()


# ============================================================
# SHOW WARNING
# ============================================================

def show_warning(
    parent,
    title="Warning",
    message="",
):
    message_box = QMessageBox(parent)

    message_box.setIcon(
        QMessageBox.Icon.Warning
    )

    message_box.setWindowTitle(tr(title))

    message_box.setText(tr(message))

    message_box.addButton(
        tr("OK"),
        QMessageBox.ButtonRole.AcceptRole,
    )

    message_box.exec()