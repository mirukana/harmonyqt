# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from matrix_client.errors import (MatrixError, MatrixHttpLibError,
                                  MatrixRequestError)
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from . import base


class Login(base.GridDialog):
    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window, "Login")

        self.info_line = base.InfoLine(self)
        self.server    = base.Field(
            self, "Server:", "scheme://domain.tld", "https://matrix.org"
        )
        self.username = base.Field(self, "Username:")
        self.password = base.Field(self, "Password:", is_password=True)
        self.remember = base.CheckBox(
            self,
            "&Remember this account",
            "Automatically login this account on startup",
            check = True,
        )
        self.login = base.AcceptButton(
            self, "&Login", self.validate,
            (self.server, self.username, self.password),
        )
        self.cancel = base.CancelButton(self)

        blank = lambda: base.BlankLine(self)

        self.add_spacer(0, 0)
        self.add_spacer(0, 3)
        # widget, from row, from col, row span, col span, align = left
        self.grid.addWidget(self.info_line,  1, 1, 1, 2)
        self.grid.addWidget(self.server,     2, 1, 1, 2)
        self.grid.addWidget(self.username,   3, 1, 1, 2)
        self.grid.addWidget(self.password,   4, 1, 1, 2)
        self.grid.addWidget(blank(),         5, 1, 1, 2)
        self.grid.addWidget(self.remember,   6, 1, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(blank(),         7, 1, 1, 2)
        self.grid.addWidget(self.login ,     8, 1, 1, 1)
        self.grid.addWidget(self.cancel,     8, 2, 1, 1)
        self.add_spacer(9, 1)
        self.add_spacer(9, 3)

        for half_col in (1, 2):
            self.grid.setColumnMinimumWidth(half_col, 144)


        self.expected_login_user_id: str = ""
        self.main_window.events.signal.new_account.connect(self.on_login)


    def validate(self, _) -> None:
        self.info_line.set_info("Logging in...")

        server   = self.server.line_edit.text()
        user     = self.username.line_edit.text()
        pw       = self.password.line_edit.text()
        remember = self.remember.isChecked()

        self.expected_login_user_id = self.main_window.accounts.login(
            server, user, pw, remember, self.on_login, self.on_error
        )


    def on_login(self, user_id: str) -> None:
        expected = self.expected_login_user_id
        if expected and user_id == expected:
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
