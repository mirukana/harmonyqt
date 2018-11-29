# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading
from typing import Dict
from enum import IntEnum

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room

from . import USER_DISPLAY_NAMES


class Levels(IntEnum):
    name            = 1
    canonical_alias = 2
    alias_0         = 3
    members         = 4
    id              = 5


class RoomDisplayNames:
    def __init__(self) -> None:
        self._rooms = {}
        self._lock  = threading.Lock()

        # (user_id, room_id): level
        self._room_name_levels: Dict[(str, str), Levels]  = {}


    def get(self, room: Room) -> str:
        user_id = room.client.user_id

        def add_return(name: str, level: Levels, same_for_everyone: bool = True
                      ) -> str:
            with self._lock:
                for_user = "any" if same_for_everyone else user_id
                self._room_name_levels[(for_user, room.room_id)] = level
                self._rooms[(for_user, room.room_id)]            = name

            return name

        try:
            return self._rooms.get(user_id, room.room_id,
                                   self._rooms["any"][room.room_id])
        except KeyError:
            if room.name:
                return add_return(room.name, Levels.name)

            if room.canonical_alias:
                return add_return(room.canonical_alias, Levels.canonical_alias)
            if room.aliases:
                return add_return(room.aliases[0], Levels.alias_0)

            try:
                members = {USER_DISPLAY_NAMES.get(u)
                           for u in room.get_joined_members()
                           if u.user_id != user_id}
            except MatrixRequestError:
                # Happens if we are a guest (invited or just not allowed)
                return add_return(room.room_id.split(":")[0], Levels.id)

            if not members:
                return add_return("Empty room", Levels.members)

            members = sorted(members)
            if len(members) == 1:
                return add_return(members[0], Levels.members, False)
            if len(members) == 2:
                return add_return(" and ".join(members), Levels.members, False)

            return add_return(f"{members[0]} and {len(members) - 1} others",
                              Levels.members,
                              False)
