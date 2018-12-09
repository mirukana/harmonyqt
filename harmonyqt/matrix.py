# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Dict

from matrix_client.client import MatrixClient
from matrix_client.user import User


def patched_get_display_name(self, room=None):
    # Original func can accidentally return None if a room is passed
    val = self.original_get_display_name(room)
    return val or self.user_id

User.original_get_display_name = User.get_display_name
User.get_display_name          = patched_get_display_name


class HMatrixClient(MatrixClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._our_users: Dict[str, User] = {}


    @property
    def h_user(self) -> User:
        if not getattr(self, "user_id", None):
            raise RuntimeError("Not logged in yet, missing user ID")

        if self.user_id not in self._our_users:
            self._our_users[self.user_id] = User(self, self.user_id)

        return self._our_users[self.user_id]
