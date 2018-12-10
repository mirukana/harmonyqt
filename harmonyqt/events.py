# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from queue import Queue
from threading import Lock
from typing import Dict

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

from .matrix import HMatrixClient


class _SignalObject(QObject):
    # User ID, room ID
    new_account  = pyqtSignal(str)
    account_gone = pyqtSignal(str)
    new_room     = pyqtSignal(str, str)
    room_rename  = pyqtSignal(str, str)
    left_room    = pyqtSignal(str, str)
    # User ID, room ID, invited by user ID, display name, name, canon alias
    new_invite = pyqtSignal(str, str, str, str, str, str)
    # User ID, room ID, new display name, new avatar URL
    account_change = pyqtSignal(str, str, str, str)


class EventManager:
    def __init__(self, window: QMainWindow) -> None:
        self.window = window
        self.signal = _SignalObject()
        # self.messages[client.user_id[room.room_id[Queue[event]]]
        self.messages: Dict[str, Dict[str, Queue]] = {}

        self._lock = Lock()

        self.window.accounts.signal.login.connect(self.add_account)
        self.window.accounts.signal.logout.connect(self.on_account_logout)


    def add_account(self, client: HMatrixClient) -> None:
        "Setup event listeners for client. Called from AccountManager.login()."
        user_id = client.user_id

        self.messages[user_id] = {}

        client.add_listener(lambda ev, u=user_id: self.on_event(u, ev))

        client.add_presence_listener(
            lambda ev, u=user_id: self.on_presence_event(u, ev))

        client.add_ephemeral_listener(
            lambda ev, u=user_id: self.on_ephemeral_event(u, ev))

        client.add_invite_listener(
            lambda rid, state, u=user_id: self.on_invite_event(u, rid, state))

        client.add_leave_listener(
            lambda rid, _, u=user_id: self.on_leave_event(u, rid))

        client.start_listener_thread()

        self.signal.new_account.emit(client.user_id)
        # TODO: room.add_state_listener


    def on_account_logout(self, user_id: str) -> None:
        self.signal.account_gone.emit(user_id)


    def on_event(self, user_id: str, event: dict) -> None:
        ev    = event
        etype = event.get("type")

        if etype == "m.room.member" and ev.get("membership") == "join":
            self.signal.new_room.emit(user_id, ev["room_id"])

            if ev.get("state_key") in self.window.accounts:
                prev = ev.get("unsigned", {}).get("prev_content")
                new  = ev.get("content")

                if prev and new and prev != new:
                    # This won't update automatically in these cases otherwise
                    user = self.window.accounts[ev["state_key"]].h_user

                    dispname         = new["displayname"] or ev["state_key"]
                    user.displayname = dispname

                    self.signal.account_change.emit(
                        ev["state_key"], ev["room_id"],
                        dispname, new["avatar_url"] or ""
                    )

        elif etype == "m.room.message":
            msg_events = self.messages[user_id]

            if ev["room_id"] not in msg_events:
                msg_events[ev["room_id"]] = Queue()

            with self._lock:
                msg_events[ev["room_id"]].put(ev)

        else:
            self._log("blue", user_id, ev, force=True)

        if etype in ("m.room.name", "m.room.canonical_alias",
                     "m.room.member"):
            self.signal.room_rename.emit(user_id, ev["room_id"])


    def on_presence_event(self, user_id: str, event: dict) -> None:
        self._log("yellow", user_id, event)


    def on_ephemeral_event(self, user_id: str, event: dict) -> None:
        self._log("purple", user_id, event)


    def on_invite_event(self, user_id: str, room_id: int, state: dict
                       ) -> None:
        invite_by = state["events"][-1]["sender"]

        name = alias = ""
        members = []

        for ev in state["events"]:
            if ev["type"] == "m.room.name":
                name = ev["content"]["name"]

            if ev["type"] == "m.room.canonical_alias":
                alias = ev["content"]["alias"]

            if ev["type"] == "m.room.member" and ev["state_key"] != user_id:
                members.append(ev["content"]["displayname"] or
                               ev["state_key"])

        dispname = name or alias

        if not dispname:
            if not members:
                dispname = "Empty room"
            elif len(members) == 1:
                dispname = members[0]
            elif len(members) == 2:
                dispname = " and ".join(members)
            else:
                members.sort()
                dispname = f"{members[0]} and {len(members) - 1} others"

        self.signal.new_invite.emit(
            user_id, room_id, invite_by, dispname, name, alias
        )


    def on_leave_event(self, user_id: str, room_id: str) -> None:
        self.signal.left_room.emit(user_id, room_id)


    def _log(self, color: str, *args, force: bool = False) -> None:
        if not force:
            return

        import json
        args = [json.dumps(arg, indent=4, sort_keys=True) for arg in args]
        nums = {"black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4,
                "purple": 5, "magenta": 5, "cyan": 6, "white": 7, "gray": 7}

        with self._lock:
            print(f"\033[3{nums[color]}m", *args, "\033[0m",
                  sep="\n", end="\n\n")
