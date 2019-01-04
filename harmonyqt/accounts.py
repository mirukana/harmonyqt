# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import base64
import hashlib
import json
import os
import platform
import threading
from collections import UserDict
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Optional
from urllib.parse import urlparse

from atomicfile import AtomicFile
from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal

from matrix_client.client import MatrixClient

LOAD_NUM_EVENTS_ON_START = 10


class _SignalObject(QObject):
    # Signals can only be emited from QObjects, but AccountManager
    # can't inherit from it because of metaclass conflict.
    login  = pyqtSignal(MatrixClient)
    logout = pyqtSignal(str)


class AccountManager(UserDict):
    def __init__(self) -> None:
        super().__init__()
        self.signal = _SignalObject()
        self._pool  = ThreadPool(8)
        self._lock  = threading.Lock()

    # Login/logout

    def login_using_config(self, path: str = "") -> None:
        def log(acc: Dict[str, str]) -> None:
            self.login(acc["server_url"], acc["user_id"], acc["password"],
                       acc["device_name"])

        def err_c(err: BaseException) -> None:
            raise err

        self._pool.map_async(log, self.config_read(path), error_callback=err_c)


    def login(self,
              server_url:    str,
              user_id:       str,
              password:      str  = "",
              device_name:   str  = "",
              add_to_config: bool = False) -> None:

        user_id = user_id.strip()

        if user_id.startswith("@") and ":" not in user_id:
            user_id = user_id[1:]

        if not user_id.startswith("@"):
            user_id = f"@{user_id}:{urlparse(server_url).netloc}"

        if user_id in self.data:
            return

        db_path, db_filename = os.path.split(self.get_crypt_db_path(user_id))

        client = MatrixClient(
            server_url,
            sync_filter_limit = LOAD_NUM_EVENTS_ON_START,
            encryption        = True,
            restore_device_id = True,
            encryption_conf   = {
                "store_conf": {"db_path": db_path, "db_name": db_filename}
            }
        )

        client.login(user_id, password, sync=False)
        client.olm_device.upload_identity_keys()

        self.data[user_id] = client
        self.signal.login.emit(client)

        system = f" on {platform.system()}".rstrip()
        system = f"{system} {platform.release()}".rstrip() \
                 if system != " on" else ""

        client.api.update_device_info(client.device_id,
                                      device_name or f"Harmony{system}")

        if add_to_config:
            self.config_add(server_url, user_id, password, device_name)


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
            return path

        base_dir = QStandardPaths.writableLocation(kind)
        path     = f"{base_dir}{os.sep}{relative_path}"
        os.makedirs(os.path.split(path)[0], exist_ok=True)

        if initial_content is not None:
            with AtomicFile(path, "w") as new:
                new.write(initial_content)

        return path


    @property
    def standard_accounts_config_path(self) -> str:
        return self._get_standard_path(
            QStandardPaths.AppConfigLocation, "accounts.json", "[]"
        )


    def get_crypt_db_path(self, user_id: str) -> str:
        safe_filename = hashlib.md5(user_id.encode("utf-8")).hexdigest()
        return self._get_standard_path(
            QStandardPaths.AppDataLocation, f"encryption/{safe_filename}.db"
        )


    # Config file operations

    def config_read(self, path: str = "") -> List[Dict[str, str]]:
        with open(path or self.standard_accounts_config_path, "r") as file:
            accs = json.loads(file.read().strip()) or []

        for acc in accs:
            pw = acc["password"]
            acc["password"] = \
                str(base64.b85decode(base64.b64decode(pw))[::-1], "utf-8")

        return accs


    def config_add(self, server_url: str, user_id: str, password: str,
                   device_name: str = "", path: str = "") -> None:
        with self._lock:
            path     = path or self.standard_accounts_config_path
            accounts = self.config_read(path)
            params   = {"server_url": server_url, "user_id":     user_id,
                        "password":   password,   "device_name": device_name,}

            for i, acc in enumerate(accounts):
                if acc["user_id"] == user_id:
                    if acc == params:
                        return

                    accounts[i] = params
                    break
            else:
                accounts.append(params)

            with AtomicFile(path, "w") as new:
                new.write(self._serialize_config(accounts))


    def config_del(self, user_id: str, path: str = "") -> None:
        with self._lock:
            path     = path or self.standard_accounts_config_path
            accounts = self.config_read(path)
            accounts = [a for a in accounts if a["user_id"] != user_id]

            with AtomicFile(path, "w") as new:
                new.write(self._serialize_config(accounts))


    @staticmethod
    def _serialize_config(accounts: List[Dict[str, str]]) -> str:
        for acc in accounts:
            pw  = acc["password"]
            byt = base64.b64encode(base64.b85encode(bytes(pw[::-1], "utf-8")))

            acc["password"] = str(byt, "utf-8")

        return json.dumps(accounts, indent=4, ensure_ascii=False)
