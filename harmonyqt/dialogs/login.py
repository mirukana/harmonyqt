# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from matrix_client.errors import (MatrixError, MatrixHttpLibError,
                                  MatrixRequestError)
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QDialog, QMainWindow, QWidget

from . import base


class RememberCheckBox(QCheckBox):
    def __init__(self, parent: QWidget) -> None:
        super().__init__("&Remember this account", parent)
        self.setToolTip("Automatically login this account on startup")
        self.setChecked(True)


class LoginButton(base.AcceptButton):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog,
                         "&Login",
                         (dialog.server, dialog.username, dialog.password))


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


class Login(base.GridDialog):
    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window, "Login")

        self.info_line = base.InfoLine(self)
        self.server    = base.Field(
            self, "Server:", "scheme://domain.tld", "https://matrix.org"
        )
        self.username = base.Field(self, "Username:")
        self.password = base.Field(self, "Password:", is_password=True)
        self.remember = RememberCheckBox(self)
        self.login    = LoginButton(self)
        self.cancel   = base.CancelButton(self)

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
