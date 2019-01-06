# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from . import LOG_PATH, PLEASE_REPORT


class Console(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        from .display import ConsoleDisplay
        self.display = ConsoleDisplay()
        self.display.make_shortcuts_accessible_from(self)

        self.about = QLabel(
            f"Unexpected errors occured.<br>"
            f"A log file is written to <em>{LOG_PATH}</em>.<br>"
            f"{PLEASE_REPORT}"
        )
        self.about.setOpenExternalLinks(True)
        self.about.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.vbox.addWidget(self.display)
        self.vbox.addWidget(self.about)
