# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import os
import threading
from collections import UserDict
from multiprocessing.pool import ThreadPool
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

from atomicfile import AtomicFile
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal

from .matrix import HMatrixClient

LOAD_NUM_EVENTS_ON_START = 20


class _SignalObject(QObject):
    # Signals can only be emited from QObjects, but AccountManager
    # can't inherit from it because of metaclass conflict.
    login  = pyqtSignal(HMatrixClient)
    logout = pyqtSignal(str)


class AccountManager(UserDict):
    def __init__(self) -> None:
        super().__init__(initialdata=None)
        self.signal = _SignalObject()
        self._pool  = ThreadPool(8)

    # Login/logout

    def login_using_config(self, path: str = "") -> None:
        for acc in self.config_read(path):
            self.login(
                server_url = acc["server_url"],
                user_id    = acc["user_id"],
                password   = acc["password"],
            )


    def login(self,
              server_url:     str,
              user_id:        str,
              password:       str,
              remember:       bool = False,
              error_callback: Optional[Callable[[BaseException], None]] = None
             ) -> str:

        user_id = user_id.strip()

        if user_id.startswith("@") and ":" not in user_id:
            user_id = user_id[1:]

        if not user_id.startswith("@"):
            user_id = f"@{user_id}:{urlparse(server_url).netloc}"

        if user_id in self.data:
            return user_id

        lock = threading.Lock()

        db_path, db_filename = os.path.split(self.crypto_db_path)

        def get_client() -> HMatrixClient:
            client = HMatrixClient(
                server_url,
                sync_filter_limit = LOAD_NUM_EVENTS_ON_START,
                encryption        = True,
                restore_device_id = True,
                encryption_conf   = {
                    "store_conf": {
                        "db_path": db_path,
                        "db_name": db_filename,
                    }
                }
            )
            client.login(user_id, password, sync=False)

            self.data[user_id] = client
            self.signal.login.emit(client)

            if remember:
                with lock:
                    self.config_add(server_url, user_id, password)

            return client

        def on_error(err: BaseException) -> None:
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


    # Standard file paths

    @staticmethod
    def _get_standard_path(kind:            QStandardPaths.StandardLocation,
                           file:            str,
                           initial_content: Optional[str] = None) -> str:
        relative_path = file.replace("/", os.sep)

        path = QStandardPaths.locate(kind, relative_path)
        if path:
            print("ex", path)
            return path

        base_dir = QStandardPaths.writableLocation(kind)
        os.makedirs(base_dir, exist_ok=True)
        path = f"{base_dir}{os.sep}{relative_path}"

        if initial_content is not None:
            with AtomicFile(path, "w") as new:
                new.write(initial_content)

        print(path)
        return path


    @property
    def standard_accounts_config_path(self) -> str:
        return self._get_standard_path(
            QStandardPaths.AppConfigLocation, "accounts.json", "[]"
        )


    @property
    def crypto_db_path(self) -> str:
        return self._get_standard_path(
            QStandardPaths.AppDataLocation, "encryption.db"
        )


    # Config file operations

    def config_read(self, path: str = "") -> List[Dict[str, str]]:
        with open(path or self.standard_accounts_config_path, "r") as file:
            return json.loads(file.read().strip()) or []


    def config_add(self, server_url: str, user_id: str, password: str,
                   path: str = "") -> None:

        path     = path or self.standard_accounts_config_path
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
        path     = path or self.standard_accounts_config_path
        accounts = self.config_read(path)
        accounts = [a for a in accounts if a["user_id"] != user_id]

        with AtomicFile(path, "w") as new:
            new.write(json.dumps(accounts, indent=4, ensure_ascii=False))
