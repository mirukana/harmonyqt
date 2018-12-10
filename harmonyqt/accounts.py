# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import os
from collections import UserDict
from multiprocessing.pool import ThreadPool
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

from atomicfile import AtomicFile
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal

from .__about__ import __pkg_name__
from .matrix import HMatrixClient

LOAD_NUM_EVENTS_ON_START = 20


class _SignalObject(QObject):
    # Signals can only be emited from QObjects, but AccountManager
    # can't inherit from it because of metaclass conflict.
    login  = pyqtSignal(HMatrixClient)
    logout = pyqtSignal(str)


class AccountManager(UserDict):
    def __init__(self, initialdata: Optional[dict] = None) -> None:
        super().__init__(initialdata)
        self.signal = _SignalObject()
        self._pool  = ThreadPool(8)


    def login(self,
              server_url:     str,
              user_id:        str,
              password:       str,
              remember:       bool = False,
              error_callback: Optional[Callable[[Exception], None]] = None
             ) -> str:

        user_id = user_id.strip()

        if user_id.startswith("@") and ":" not in user_id:
            user_id = user_id[1:]

        if not user_id.startswith("@"):
            user_id = f"@{user_id}:{urlparse(server_url).netloc}"

        if user_id in self.data:
            return user_id

        def get_client() -> HMatrixClient:
            client = HMatrixClient(
                server_url, sync_filter_limit=LOAD_NUM_EVENTS_ON_START
            )
            client.login(user_id, password, sync=False)

            self.data[user_id] = client
            self.signal.login.emit(client)

            if remember:
                self.config_add(server_url, user_id, password)

            return client

        def on_error(err: Exception) -> None:
            # Without this handler, exceptions will be silently ignored
            raise err

        self._pool.apply_async(get_client,
                               error_callback = error_callback or on_error)
        return user_id


    def remove(self, user_id: str) -> None:
        if user_id not in self.data:
            return

        self.signal.logout.emit(user_id)
        self._pool.apply_async(self.data[user_id].logout)
        del self.data[user_id]
        self.config_del(user_id)


    @staticmethod
    def get_config_path(path: str = "") -> str:
        path_suffix = f"{__pkg_name__}{os.sep}accounts.json"
        loc         = QStandardPaths.ConfigLocation

        path = path or QStandardPaths.locate(loc, path_suffix)

        if path:
            return path

        base_dir = QStandardPaths.writableLocation(loc)

        if not base_dir:
            raise OSError("Cannot determine writable configuration dir.")

        os.makedirs(base_dir, exist_ok=True)
        path = f"{base_dir}{os.sep}{path_suffix}"

        with AtomicFile(path, "w") as new:
            new.write("[]")

        return path


    def config_read(self, path: str = "") -> List[Dict[str, str]]:
        with open(self.get_config_path(path), "r") as file:
            content = file.read().strip()
            return json.loads(content) or []


    def login_using_config(self, path: str = "") -> None:
        for acc in self.config_read(path):
            self.login(**acc)


    def config_add(self, server_url: str, user_id: str, password: str,
                   path: str = "") -> None:

        path     = self.get_config_path(path)
        accounts = self.config_read(path)
        params   = {"server_url": server_url, "user_id": user_id,
                    "password":   password}

        for acc in accounts:
            if acc["user_id"] == user_id:
                return

        accounts.append(params)

        with AtomicFile(path, "w") as new:
            new.write(json.dumps(accounts, indent=4, ensure_ascii=False))


    def config_del(self, user_id: str, path: str = "") -> None:
        path     = self.get_config_path(path)
        accounts = self.config_read(path)
        accounts = [a for a in accounts if a["user_id"] != user_id]

        with AtomicFile(path, "w") as new:
            new.write(json.dumps(accounts, indent=4, ensure_ascii=False))
