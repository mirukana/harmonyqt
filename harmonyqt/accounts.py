# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import os
from collections import UserDict
from multiprocessing.pool import ThreadPool
from typing import Optional

from matrix_client.client import MatrixClient
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

from .__about__ import __pkg_name__

LOAD_NUM_EVENTS_ON_START = 20


class _SignalObject(QObject):
    # Signals can only be emited from QObjects, but AccountManager
    # can't inherit from it because of metaclass conflict.
    login = pyqtSignal(MatrixClient)


class AccountManager(UserDict):
    def __init__(self,
                 window:      Optional[QMainWindow] = None,
                 initialdata: Optional[dict]        = None) -> None:
        super().__init__(initialdata)
        self.window   = window
        self.signal   = None
        self._pool    = ThreadPool(8)

        if self.window:
            self.signal = _SignalObject()


    def login(self, server_url: str, user_id: str, password: str) -> None:
        def get_client() -> MatrixClient:
            client = MatrixClient(server_url,
                                  sync_filter_limit=LOAD_NUM_EVENTS_ON_START)
            client.login(user_id, password, sync=False)
            self.signal.login.emit(client)
            self.data[user_id] = client

        self._pool.apply_async(get_client)


    def login_using_config(self, path: Optional[str] = None) -> None:
        path_suffix = f"{__pkg_name__}{os.sep}accounts.json"

        path = path or QStandardPaths.locate(
            QStandardPaths.ConfigLocation, path_suffix
        )

        with open(path, "r") as file:
            accounts = json.loads(file.read())

        for acc in accounts:
            self.login(**acc)
