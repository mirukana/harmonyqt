# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading
from typing import Union

from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room
from matrix_client.user import User


class _DisplayNamesCache:
    def __init__(self) -> None:
        self._users      = self._rooms      = {}
        self._users_lock = self._rooms_lock = threading.Lock()


    def user(self, obj: Union[MatrixClient, User]) -> str:
        if isinstance(obj, MatrixClient):
            obj = User(obj, obj.user_id)

        try:
            return self._users[obj.user_id]
        except KeyError:
            name = obj.get_display_name()
            with self._users_lock:
                self._users[obj.user_id] = name
            return name


    def room(self, room: Room) -> str:
        def add_return(name: str, same_for_everyone: bool = True) -> str:
            with self._rooms_lock:
                for_user = "any" if same_for_everyone else room.client.user_id
                self._rooms[(for_user, room.room_id)] = name
            return name

        try:
            return self._rooms.get((room.client.user_id, room.room_id),
                                   self._rooms["any"][room.room_id])
        except KeyError:
            room.update_room_name()
            if room.name:
                return add_return(room.name)

            room.update_aliases()
            if room.canonical_alias:
                return add_return(room.canonical_alias)
            if room.aliases:
                return add_return(room.aliases[0])

            try:
                members = {self.user(u) for u in room.get_joined_members() if
                           u.user_id != room.client.user_id}
            except MatrixRequestError:
                # Happens if we are a guest (invited or just not allowed)
                return room.room_id.split(":")[0]

            if not members:
                return "Empty room"

            members = sorted(members)
            if len(members) == 1:
                return add_return(members[0], False)
            if len(members) == 2:
                return add_return(" and ".join(members), False)

            return add_return(f"{members[0]} and {len(members) - 1} others",
                              False)

DISPLAY_NAMES = _DisplayNamesCache()
