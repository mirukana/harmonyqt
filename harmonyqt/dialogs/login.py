# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Optional

from matrix_client.errors import (MatrixError, MatrixHttpLibError,
                                  MatrixRequestError)
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QGridLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QSizePolicy,
                             QSpacerItem, QWidget)

from .. import STYLESHEET, main


class InfoLine(QLabel):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setProperty("error", False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.hide()


    def _set_to(self, text: Optional[str] = None) -> None:
        self.setText(text)
        if text:
            self.show()
        else:
            self.hide()
        self.style().unpolish(self)
        self.style().polish(self)


    def clear(self) -> None:
        self.setProperty("error", False)
        self._set_to(None)


    def set_info(self, text: str) -> None:
        self.setProperty("error", False)
        self._set_to(text)


    def set_err(self, text: str) -> None:
        self.setProperty("error", True)
        self._set_to(text)


class Field(QWidget):
    def __init__(self,
                 parent:       QWidget,
                 label:        str,
                 placeholder : str  = "",
                 default_text: str  = "",
                 is_password:  bool = False) -> None:
        super().__init__(parent)

        self.grid = QGridLayout(self)

        self.label = QLabel(label, parent)
        self.grid.addWidget(self.label, 0, 0)

        self.line_edit = QLineEdit(parent)
        self.line_edit.setDragEnabled(True)
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setText(default_text)
        if is_password:
            self.line_edit.setEchoMode(QLineEdit.Password)
        self.grid.addWidget(self.line_edit, 1, 0)


class RememberCheckBox(QCheckBox):
    def __init__(self, parent: QWidget) -> None:
        super().__init__("&Remember this account", parent)
        self.setToolTip("Automatically login this account on startup")
        self.setChecked(True)


class LoginButton(QPushButton):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(main.get_icon("accept_small.png"), "&Login", dialog)
        self.dialog = dialog
        self.setEnabled(False)

        self.text_in_fields = {}

        # Button will be disabled until all these fields have a value:
        for field in ("server", "username", "password"):
            line_edit = getattr(self.dialog, field).line_edit

            self.text_in_fields[field] = bool(line_edit.text())

            line_edit.textChanged.connect(
                lambda txt, f=field: self.on_field_change(f, txt)
            )

        self.clicked.connect(self.on_click)


    def on_field_change(self, field: str, text: str) -> None:
        self.text_in_fields[field] = bool(text)
        self.setEnabled(
            all((has_text for field, has_text in self.text_in_fields.items()))
        )


    def on_click(self, _) -> None:
        self.dialog.info_line.set_info("Logging in...")

        server   = self.dialog.server.line_edit.text()
        user     = self.dialog.username.line_edit.text()
        pw       = self.dialog.password.line_edit.text()
        remember = self.dialog.remember.isChecked()

        self.dialog.main_window.accounts.login(
            server, user, pw, remember,
            self.dialog.on_login, self.dialog.on_error
        )


class CancelButton(QPushButton):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(main.get_icon("cancel_small.png"), "&Cancel", dialog)
        self.dialog = dialog
        self.clicked.connect(self.on_click)


    def on_click(self, _) -> None:
        self.dialog.done(1)


class Login(QDialog):
    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window)
        self.main_window = main_window

        self.setStyleSheet(STYLESHEET)
        self.setWindowTitle("Harmony - Login")
        self.setWindowOpacity(0.8)

        self.info_line = InfoLine(self)
        self.server     = Field(
            self, "Server:", "scheme://domain.tld", "https://matrix.org"
        )
        self.username = Field(self, "Username:")
        self.password = Field(self, "Password:", is_password=True)
        self.remember = RememberCheckBox(self)
        self.login    = LoginButton(self)
        self.cancel   = CancelButton(self)

        self.grid = QGridLayout(self)
        self.add_spacer(0, 0)
        self.add_spacer(0, 3)
        # widget, from row, from col, row span, col span, align = left
        self.grid.addWidget(self.info_line,  1, 1, 1, 2)
        self.grid.addWidget(self.server,     2, 1, 1, 2)
        self.grid.addWidget(self.username,   3, 1, 1, 2)
        self.grid.addWidget(self.password,   4, 1, 1, 2)
        self.grid.addWidget(QWidget(),       5, 1, 1, 2)
        self.grid.addWidget(self.remember,   6, 1, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(QWidget(),       7, 1, 1, 2)
        self.grid.addWidget(self.login ,     8, 1, 1, 1)
        self.grid.addWidget(self.cancel,     8, 2, 1, 1)
        self.add_spacer(9, 1)
        self.add_spacer(9, 3)

        for blank_row in (5, 7):
            self.grid.setRowMinimumHeight(blank_row, 16)

        for half_col in (1, 2):
            self.grid.setColumnMinimumWidth(half_col, 144)


    def add_spacer(self, row: int, col: int) -> None:
        spc = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid.addItem(spc, row, col)


    def open_modeless(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()


    def on_login(self, _) -> None:
        self.done(0)


    def on_error(self, err: Exception) -> None:
        if isinstance(err, MatrixRequestError):
            self.info_line.set_err("Invalid username or password")

        elif isinstance(err, MatrixHttpLibError):
            self.info_line.set_err("Unreachable server")

        elif isinstance(err, MatrixError):
            if "No scheme" in str(err):
                self.info_line.set_err("Server is missing a scheme://")

            elif "Invalid home server" in str(err):
                self.info_line.set_err("Invalid server URL")

            else:
                raise err

        else:
            raise err
