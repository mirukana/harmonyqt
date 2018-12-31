# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from multiprocessing.pool import ThreadPool

from matrix_client.errors import (
    MatrixError, MatrixHttpLibError, MatrixRequestError
)
from PyQt5.QtCore import Qt, pyqtSignal

from . import base
from .. import main_window


class Login(base.GridDialog):
    login_done_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("Login")
        self._pool = ThreadPool(1)

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

        self.username.text_edit.setFocus()

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

        self.login_done_signal.connect(self.on_login)


    def validate(self, _) -> None:
        self.info_line.set_info("Logging in...")

        self._pool.apply_async(
            func = main_window().accounts.login,
            kwds = {
                "server_url":    self.server.get_text(),
                "user_id":       self.username.get_text(),
                "password":      self.password.get_text(),
                "add_to_config": self.remember.isChecked(),
            },
            callback       = lambda *_: self.login_done_signal.emit(),
            error_callback = self.on_error,
        )


    def on_login(self) -> None:
        self.done(0)


    def on_error(self, err: BaseException) -> None:
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
