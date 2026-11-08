import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import (
    add_combo_item,
    select_combo_data,
)

from gui.widgets import (
    PageHeader,
    PrimaryButton,
    SecondaryButton,
    show_error,
)


# ============================================================
# SETTINGS STORAGE
# ============================================================

SETTINGS_FILE = Path("user_settings.json")


DEFAULT_SETTINGS = {
    "appearance": "Dark",
    "color_scheme": "Purple + Pink",
    "language": "English",
}


COLOR_SCHEMES = {
    "Blue + Green": {
        "primary": "#3B82F6",
        "secondary": "#10B981",
    },
    "Purple + Pink": {
        "primary": "#8B5CF6",
        "secondary": "#EC4899",
    },
    "Yellow + Orange": {
        "primary": "#EAB308",
        "secondary": "#F97316",
    },
}


APPEARANCE_MODES = (
    "Dark",
    "Light",
    "System",
    "AMOLED",
)


LANGUAGES = (
    "English",
    "Persian",
)


# ============================================================
# SETTINGS PAGE
# ============================================================

class SettingsPage(QWidget):

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._loading = False

        self.settings = self.load_settings()

        self.setup_ui()
        self.load_settings_into_ui()

    # ========================================================
    # LOAD SETTINGS
    # ========================================================

    def load_settings(self):
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS.copy()

        try:
            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                loaded_settings = json.load(file)

            settings = DEFAULT_SETTINGS.copy()
            settings.update(loaded_settings)

            return settings

        except Exception:
            return DEFAULT_SETTINGS.copy()

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def save_settings(self, notify=True):
        try:
            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    self.settings,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except Exception as error:
            if notify:
                show_error(
                    self,
                    "Unable to save settings",
                    str(error),
                )

            return False

        return True

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):
        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(0, 0, 0, 0)

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
        layout.setSpacing(24)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = PageHeader(
            "Settings",
            "Customize StudyFlow to match your style.",
        )

        layout.addWidget(header)

        # ----------------------------------------------------
        # APPEARANCE CARD
        # ----------------------------------------------------

        appearance_card = QFrame()
        appearance_card.setObjectName("dataCard")

        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setContentsMargins(22, 20, 22, 20)
        appearance_layout.setSpacing(14)

        appearance_title = QLabel("🖥 Appearance")
        appearance_title.setStyleSheet(
            "font-size: 18px; font-weight: 700;"
        )

        appearance_description = QLabel(
            "Choose how StudyFlow looks on your screen."
        )
        appearance_description.setObjectName("subtitle")

        appearance_layout.addWidget(appearance_title)
        appearance_layout.addWidget(appearance_description)
        appearance_layout.addSpacing(6)

        self.appearance_group = QButtonGroup(self)

        self.appearance_buttons = {}

        for mode in APPEARANCE_MODES:
            button = QRadioButton(mode)

            self.appearance_group.addButton(button)

            self.appearance_buttons[mode] = button

            appearance_layout.addWidget(button)

        self.appearance_group.buttonClicked.connect(
            self.on_ui_changed
        )

        layout.addWidget(appearance_card)

        # ----------------------------------------------------
        # COLOR CARD
        # ----------------------------------------------------

        color_card = QFrame()
        color_card.setObjectName("dataCard")

        color_layout = QVBoxLayout(color_card)
        color_layout.setContentsMargins(22, 20, 22, 20)
        color_layout.setSpacing(14)

        color_title = QLabel("🎨 Color Theme")
        color_title.setStyleSheet(
            "font-size: 18px; font-weight: 700;"
        )

        color_description = QLabel(
            "Choose your favorite StudyFlow color palette."
        )
        color_description.setObjectName("subtitle")

        self.color_scheme_input = QComboBox()

        for scheme_name in COLOR_SCHEMES:
            add_combo_item(
                self.color_scheme_input,
                scheme_name,
                scheme_name,
            )

        self.color_preview = QFrame()
        self.color_preview.setFixedHeight(55)
        self.color_preview.setObjectName("colorPreview")

        self.color_scheme_input.currentIndexChanged.connect(
            self.on_color_changed
        )

        color_layout.addWidget(color_title)
        color_layout.addWidget(color_description)
        color_layout.addSpacing(6)
        color_layout.addWidget(self.color_scheme_input)
        color_layout.addWidget(self.color_preview)

        layout.addWidget(color_card)

        # ----------------------------------------------------
        # LANGUAGE CARD
        # ----------------------------------------------------

        language_card = QFrame()
        language_card.setObjectName("dataCard")

        language_layout = QVBoxLayout(language_card)
        language_layout.setContentsMargins(22, 20, 22, 20)
        language_layout.setSpacing(14)

        language_title = QLabel("🌐 Language")
        language_title.setStyleSheet(
            "font-size: 18px; font-weight: 700;"
        )

        language_description = QLabel(
            "Select the interface language."
        )
        language_description.setObjectName("subtitle")

        self.language_input = QComboBox()

        for language in LANGUAGES:
            add_combo_item(
                self.language_input,
                language,
                language,
            )

        self.language_input.currentIndexChanged.connect(
            self.on_ui_changed
        )

        language_layout.addWidget(language_title)
        language_layout.addWidget(language_description)
        language_layout.addSpacing(6)
        language_layout.addWidget(self.language_input)

        layout.addWidget(language_card)

        # ----------------------------------------------------
        # INFO CARD
        # ----------------------------------------------------

        info_card = QFrame()
        info_card.setObjectName("dataCard")

        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(22, 20, 22, 20)
        info_layout.setSpacing(8)

        info_title = QLabel("ℹ StudyFlow")
        info_title.setStyleSheet(
            "font-size: 18px; font-weight: 700;"
        )

        version_label = QLabel("Version 1.0")
        version_label.setObjectName("subtitle")

        info_text = QLabel(
            "A personal academic management "
            "application for organizing courses, "
            "assignments and study sessions."
        )
        info_text.setObjectName("subtitle")
        info_text.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(version_label)
        info_layout.addWidget(info_text)

        layout.addWidget(info_card)

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        actions = QHBoxLayout()

        reset_button = SecondaryButton("↺ Reset")
        reset_button.clicked.connect(self.reset_settings)

        save_button = PrimaryButton("💾 Save Settings")
        save_button.clicked.connect(
            self.save_and_apply_settings
        )

        actions.addWidget(reset_button)
        actions.addStretch()
        actions.addWidget(save_button)

        layout.addLayout(actions)

        layout.addStretch()

    # ========================================================
    # LOAD INTO UI
    # ========================================================

    def load_settings_into_ui(self):
        self._loading = True

        try:
            appearance = self.settings.get(
                "appearance",
                DEFAULT_SETTINGS["appearance"],
            )

            button = self.appearance_buttons.get(appearance)

            if button is not None:
                button.setChecked(True)

            select_combo_data(
                self.color_scheme_input,
                self.settings.get(
                    "color_scheme",
                    DEFAULT_SETTINGS["color_scheme"],
                ),
            )

            select_combo_data(
                self.language_input,
                self.settings.get(
                    "language",
                    DEFAULT_SETTINGS["language"],
                ),
            )

            self.update_color_preview()

        finally:
            self._loading = False

    # ========================================================
    # COLOR PREVIEW
    # ========================================================

    def update_color_preview(self):
        scheme_name = self.color_scheme_input.currentData()

        scheme = COLOR_SCHEMES.get(scheme_name)

        if scheme is None:
            return

        self.color_preview.setStyleSheet(
            f"""
            QFrame#colorPreview {{
                border-radius: 12px;
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 0,
                    stop: 0 {scheme["primary"]},
                    stop: 1 {scheme["secondary"]}
                );
            }}
            """
        )

    def on_color_changed(self, _index):
        self.update_color_preview()
        self.on_ui_changed()

    # ========================================================
    # COLLECT SETTINGS
    # ========================================================

    def get_selected_appearance(self):
        for mode, button in self.appearance_buttons.items():
            if button.isChecked():
                return mode

        return DEFAULT_SETTINGS["appearance"]

    def collect_settings(self):
        return {
            "appearance": self.get_selected_appearance(),
            "color_scheme": (
                self.color_scheme_input.currentData()
                or DEFAULT_SETTINGS["color_scheme"]
            ),
            "language": (
                self.language_input.currentData()
                or DEFAULT_SETTINGS["language"]
            ),
        }

    # ========================================================
    # AUTO APPLY / SAVE
    # ========================================================

    def on_ui_changed(self, *_args):
        if self._loading:
            return

        self.settings = self.collect_settings()

        self.save_settings(notify=False)

        self.settings_changed.emit(
            self.settings.copy()
        )

    def save_and_apply_settings(self):
        self.settings = self.collect_settings()

        success = self.save_settings()

        if not success:
            return

        self.settings_changed.emit(
            self.settings.copy()
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()

        self.load_settings_into_ui()

        self.save_settings()

        self.settings_changed.emit(
            self.settings.copy()
        )
