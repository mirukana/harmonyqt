# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading
from typing import Union

from matrix_client.client import MatrixClient
from matrix_client.user import User


class UserDisplayNames:
    def __init__(self) -> None:
        self._users = {}
        self._lock  = threading.Lock()


    def get(self, obj: Union[MatrixClient, User]) -> str:
        if isinstance(obj, MatrixClient):
            obj = User(obj, obj.user_id)

        try:
            return self._users[obj.user_id]
        except KeyError:
            name = obj.get_display_name()
            with self._lock:
                self._users[obj.user_id] = name
            return name
