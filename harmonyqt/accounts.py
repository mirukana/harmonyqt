# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import base64
import hashlib
import json
import os
import threading
from collections import UserDict
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Optional
from urllib.parse import urlparse

from atomicfile import AtomicFile
from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal

from matrix_client.client import MatrixClient
from matrix_client.crypto.olm_device import OlmDevice
from matrix_client.device import Device
from matrix_client.errors import RoomEventDecryptError

from harmonyqt.commands.devices import set_default_device_name_if_empty

LOAD_NUM_EVENTS_ON_START = 10

_CONFIG_LOCK   = threading.Lock()
_CRYPT_DB_LOCK = threading.Lock()


class _SignalObject(QObject):
    # Signals can only be emited from QObjects, but AccountManager
    # can't inherit from it because of metaclass conflict.
    login  = pyqtSignal(MatrixClient)
    logout = pyqtSignal(str)

    decrypt_error = pyqtSignal(str, RoomEventDecryptError)  # User ID, error


class AccountManager(UserDict):
    def __init__(self) -> None:
        super().__init__()
        self.signals: _SignalObject = _SignalObject()
        self._pool:   ThreadPool    = ThreadPool(8)


    # Login/logout

    def login_using_config(self, path: str = "") -> None:
        def log(acc: Dict[str, str]) -> None:
            self.login(acc["server_url"], acc["user_id"], acc["password"])

        def err_c(err: BaseException) -> None:
            raise err

        self._pool.map_async(log, self.config_read(path), error_callback=err_c)


    def login(self,
              server_url:    str,
              user_id:       str,
              password:      str  = "",
              add_to_config: bool = False) -> None:

        user_id = user_id.strip()

        if user_id.startswith("@") and ":" not in user_id:
            user_id = user_id[1:]

        if not user_id.startswith("@"):
            user_id = f"@{user_id}:{urlparse(server_url).netloc}"

        if user_id in self.data:
            return

        new_crypt_db = not os.path.exists(self.get_crypt_db_path(user_id))

        db_path, db_filename = os.path.split(self.get_crypt_db_path(user_id))

        client = MatrixClient(
            server_url,
            sync_filter_limit = LOAD_NUM_EVENTS_ON_START,
            encryption        = True,
            restore_device_id = True,
            encryption_conf   = {
                "load_all":   True,
                "store_conf": {"db_path": db_path, "db_name": db_filename}
            },
            decrypt_error_handler = lambda e: \
                self.signals.decrypt_error.emit(user_id, e)
        )

        client.login(user_id, password, sync=False)

        self.data[user_id] = client
        self.signals.login.emit(client)

        set_default_device_name_if_empty(client)

        if new_crypt_db:
            self.trust_our_other_accounts(client)

        if add_to_config:
            self.config_add(server_url, user_id, password)


    def remove(self, user_id: str) -> None:
        if user_id not in self.data:
            return

        self.signals.logout.emit(user_id)
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


    # Crypto database operations

    def trust_our_other_accounts(self, client: MatrixClient) -> None:
        to_add_for_client: Dict[str, Dict[str, Device]] = {}

        def trust(dev: Device) -> Device:
            dev.verified    = True
            dev.blacklisted = False
            dev.ignored     = False
            return dev

        our_dev: OlmDevice = trust(client.olm_device)

        with _CRYPT_DB_LOCK:
            for other in self.data.values():
                if other.user_id == client.user_id:
                    continue

                other_dev   = other.olm_device
                to_add_devs = to_add_for_client.setdefault(other.user_id, {})
                to_add_devs[other_dev.device_id] = other_dev

                other_dev.db.save_device_keys(
                    {our_dev.user_id: {our_dev.device_id: our_dev}}
                )
                other_dev.db.load_device_keys(other.api, other_dev.device_keys)

            our_dev.db.save_device_keys(to_add_for_client)
            our_dev.db.load_device_keys(client.api, our_dev.device_keys)


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
                   path: str = "") -> None:
        with _CONFIG_LOCK:
            path     = path or self.standard_accounts_config_path
            accounts = self.config_read(path)
            params   = {"server_url": server_url, "user_id": user_id,
                        "password":   password}

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
        with _CONFIG_LOCK:
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
