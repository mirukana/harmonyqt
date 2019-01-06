# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import traceback

from PyQt5.QtWidgets import QMessageBox, QTextEdit

from . import PLEASE_REPORT, LOG_PATH


class ErrorBox(QMessageBox):
    def __init__(self, trace_str: str) -> None:
        super().__init__()
        try:
            from .. import main_window
            window = main_window()
            if hasattr(window, "theme"):
                self.setStyleSheet(window.theme.style("interface"))
                self.setWindowOpacity(0.9)
        except Exception:
            traceback.print_exc()

        self.setWindowTitle("Harmony - Unexpected error")
        self.setText("An unexpected error occured.")
        self.setInformativeText(f"A log file has been written to:<br>"
                                f"<em>{LOG_PATH}</em>.<br><br>"
                                f"{PLEASE_REPORT}")
        self.setDetailedText(trace_str)
        self.setIcon(QMessageBox.Warning)
        self.setStandardButtons(QMessageBox.Close)

        for details in self.findChildren(QTextEdit):
            details.setFixedSize(640, 360)

        for button in self.buttons():
            if self.buttonRole(button) == QMessageBox.ActionRole:
                button.click()
                break


class FatalErrorBox(ErrorBox):
    def __init__(self, trace_str: str) -> None:
        super().__init__(trace_str)
        self.setWindowTitle("Harmony - Fatal error")
        self.setText("Fatal error, execution halted!")
        self.setIcon(QMessageBox.Critical)
