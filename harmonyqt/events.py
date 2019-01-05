# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from multiprocessing.pool import ThreadPool
from threading import Lock
from typing import Dict, Set

from PyQt5.QtCore import QDateTime, QObject, pyqtSignal

from matrix_client.client import MatrixClient

from . import main_window, message


class _SignalObject(QObject):
    # User ID, event
    new_event        = pyqtSignal(str, dict)
    new_unique_event = pyqtSignal(str, dict)

    new_message = pyqtSignal(message.Message)

    # User ID
    new_account  = pyqtSignal(str)
    account_gone = pyqtSignal(str)
    # User ID, room ID, new display name, new avatar URL
    account_change = pyqtSignal(str, str, str, str)

    # User ID, room ID
    new_room    = pyqtSignal(str, str)
    room_rename = pyqtSignal(str, str)
    left_room   = pyqtSignal(str, str)
    # User ID, room ID, invited by user ID, display name, name, canon alias
    new_invite = pyqtSignal(str, str, str, str, str, str)


class EventManager:
    def __init__(self) -> None:
        self._pool: ThreadPool = ThreadPool(1)

        self.start_ms_since_epoch: int = \
            QDateTime.currentDateTime().toMSecsSinceEpoch()

        self.signal = _SignalObject()

        self._added_rooms:   Dict[str, Set[str]] = {}  # {user_id: {room_id}}
        self._got_event_ids: Dict[str, Set[str]] = {}  # {user_id: {event_id}}

        self._lock = Lock()

        main_window().accounts.signal.login.connect(self.add_account)
        main_window().accounts.signal.logout.connect(self.on_account_logout)
        self.signal.new_room.connect(self.add_room_listeners)


    def add_account(self, client: MatrixClient) -> None:
        "Setup event listeners for client. Called from AccountManager.login()."
        user_id = client.user_id

        client.add_listener(lambda ev, u=user_id: self.process_event(u, ev))

        client.add_presence_listener(
            lambda ev: self.on_presence_event(user_id, ev))

        client.add_ephemeral_listener(
            lambda ev: self.on_ephemeral_event(user_id, ev))

        client.add_invite_listener(
            lambda rid, state: self.on_invite_event(user_id, rid, state))

        client.add_leave_listener(
            lambda rid, _: self.on_leave_event(user_id, rid))

        client.start_listener_thread()

        self.signal.new_account.emit(client.user_id)


    def add_room_listeners(self, user_id: str, room_id: str) -> None:
        room = main_window().accounts[user_id].rooms[room_id]

        room.add_listener(
            lambda _, ev: self.process_event(user_id, ev))

        room.add_ephemeral_listener(
            lambda _, ev: self.on_ephemeral_event(user_id, ev))

        room.add_state_listener(
            lambda ev: self.on_state_event(user_id, ev))


    def on_account_logout(self, receiver_id: str) -> None:
        self.signal.account_gone.emit(receiver_id)


    def is_old_event(self, event: dict) -> bool:
        return event["origin_server_ts"] < self.start_ms_since_epoch


    def process_event(self, receiver_id: str, event: dict) -> None:
        self.signal.new_event.emit(receiver_id, event)

        ev        = event
        etype     = event["type"]
        room_id   = event["room_id"]
        old       = self.is_old_event(event)

        with self._lock:
            received = self._got_event_ids.setdefault(receiver_id, set())
            if ev["event_id"] in received:
                return
            received.add(ev["event_id"])

            added_for_recv = self._added_rooms.setdefault(receiver_id, set())
            if room_id not in added_for_recv:
                added_for_recv.add(room_id)
                self.signal.new_room.emit(receiver_id, room_id)

        self.signal.new_unique_event.emit(receiver_id, event)

        if etype == "m.room.message":
            self._pool.apply_async(
                func = self.on_new_message,
                args = (receiver_id, event), error_callback=self._on_emit_err,
            )

        if old:
            return

        if etype == "m.room.member" and ev.get("membership") == "join":
            if ev.get("state_key") in main_window().accounts:
                prev = ev.get("unsigned", {}).get("prev_content")
                new  = ev.get("content")

                if prev and new and prev != new:
                    # This won't update automatically in these cases otherwise
                    user = main_window().accounts[ev["state_key"]].user

                    dispname         = new["displayname"] or ev["state_key"]
                    user.displayname = dispname

                    self.signal.account_change.emit(
                        ev["state_key"], room_id,
                        dispname, new["avatar_url"] or ""
                    )

        if etype in ("m.room.name", "m.room.canonical_alias", "m.room.member"):
            self.signal.room_rename.emit(receiver_id, room_id)


    def on_new_message(self, receiver_id: str, event: dict) -> None:
        ev = event

        try:
            if ev["content"]["msgtype"] != "m.text":
                raise RuntimeError
        except Exception:
            print("\nUnsupported msg event:\n", json.dumps(ev, indent=4))
            return

        msg = message.Message(
            sender_id      = ev["sender"],
            receiver_id    = receiver_id,
            room_id        = ev["room_id"],
            markdown       = ev["content"]["body"],
            html           = ev["content"].get("formatted_body", ""),
            ms_since_epoch = ev["origin_server_ts"],
        )
        self.signal.new_message.emit(msg)


    @staticmethod
    def _on_emit_err(err: BaseException) -> None:
        raise err


    def on_presence_event(self, receiver_id: str, event: dict) -> None:
        self._log("yellow", "unhandled presence event", receiver_id, event)


    def on_ephemeral_event(self, receiver_id: str, event: dict) -> None:
        self._log("purple", "unhandled ephemeral event", receiver_id, event)


    def on_state_event(self, receiver_id: str, event: dict) -> None:
        self._log("cyan", "unhandled state event", receiver_id, event)


    def on_invite_event(self, receiver_id: str, room_id: int, state: dict
                       ) -> None:
        invite_by = state["events"][-1]["sender"]

        name = alias = ""
        members = []

        for ev in state["events"]:
            etype = ev["type"]

            if etype == "m.room.name":
                name = ev["content"]["name"]

            if etype == "m.room.canonical_alias":
                alias = ev["content"]["alias"]

            if etype == "m.room.member" and ev["state_key"] != receiver_id:
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
            receiver_id, room_id, invite_by, dispname, name, alias
        )


    def on_leave_event(self, receiver_id: str, room_id: str) -> None:
        with self._lock:
            self._added_rooms[receiver_id].discard(room_id)
            self.signal.left_room.emit(receiver_id, room_id)


    def _log(self, color: str, *args, force: bool = True) -> None:
        if not force:
            return

        jsons = [json.dumps(arg, indent=4, sort_keys=True) for arg in args]
        nums  = {"black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4,
                 "purple": 5, "magenta": 5, "cyan": 6, "white": 7, "gray": 7}

        with self._lock:
            print(f"\033[3{nums[color]}m", *jsons, "\033[0m",
                  sep="\n", end="\n\n")
