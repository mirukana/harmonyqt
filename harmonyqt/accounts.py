# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import os
from collections import namedtuple
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Optional
from urllib.parse import urlparse

from matrix_client.client import MatrixClient
from matrix_client.user import User
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QStandardPaths

from .__about__ import __pkg_name__

AccountTuple = namedtuple("AccountTuple", ("client", "user"))

CredentialsType    = List[Dict[str, str]]
LoggedAccountsType = Dict[str, AccountTuple]

LOAD_NUM_EVENTS_ON_START = 20


def load_json(path: Optional[str] = None) -> CredentialsType:
    path_suffix = f"{__pkg_name__}{os.sep}accounts.json"

    path = path or QStandardPaths.locate(
        QStandardPaths.ConfigLocation, path_suffix
    )
    try:
        with open(path, "r") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        paths = QStandardPaths.standardLocations(QStandardPaths.ConfigLocation)
        paths = [f"{p}{os.sep}{path_suffix}" for p in paths]

        example = [{"server_url": "https://matrix.org",
                    "user_id":    "@foo:matrix.org",
                    "password":   "1234"}]

        example2 = [example[0], example[0].copy()]
        example2[1]["user_id"]  = "@account2:matrix.org"
        example2[1]["password"] = "abc456"

        example  = json.dumps(example)
        example2 = json.dumps(example2).replace("}, {", "},\n   {")

        raise FileNotFoundError(
            f"\nMissing accounts config file. "
            f"Possible locations:\n  {str(paths).strip('[]')}\n\n"
            f"Example format: \n  {example}\n\n"
            f"Example with two accounts: \n  {example2}"
        )


def login(accounts:  CredentialsType = None,
          device_id: str             = "harmonyqt") -> LoggedAccountsType:

    result = {}

    def login_account(server: str, user: str, pw: str) -> None:
        # Don't sync at login, wait for the EventManager to start listening.
        client = MatrixClient(server,
                              sync_filter_limit=LOAD_NUM_EVENTS_ON_START)

        if not user.startswith("@"):
            netloc = urlparse(server).netloc
            user   = f"@{user}:{netloc}"

        client.login(username=user, password=pw, device_id=device_id,
                     sync=False)

        user                 = User(client, user)
        result[user.user_id] = AccountTuple(client=client, user=user)

    accounts = accounts or load_json()
    args     = [(acc["server_url"], acc["user_id"], acc["password"])
                for acc in accounts]

    ThreadPool(6).starmap(login_account, args)
    return result
