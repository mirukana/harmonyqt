# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import time
from collections import UserDict
from multiprocessing.pool import ThreadPool
from queue import PriorityQueue

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime

from . import main_window


class MessageProcessor(UserDict):
    def __init__(self) -> None:
        # Dict structure: {user_id: {room_id: Queue}}
        super().__init__()
        self._pool = ThreadPool(8)

        ev_sig = main_window().events.signal
        ev_sig.new_account.connect(self.on_new_account)
        ev_sig.new_room.connect(self.on_new_room)
        ev_sig.new_message.connect(self.on_new_message)


    def on_new_account(self, user_id: str) -> None:
        self.data[user_id] = {}

    def on_new_room(self, user_id: str, room_id: str) -> None:
        self.data[user_id][room_id] = PriorityQueue()

    def on_new_message(self, user_id: str, room_id: str, event: dict) -> None:
        self._pool.apply_async(self.treat_message, (user_id, room_id, event),
                               error_callback=self.on_treat_error)


    def treat_message(self, user_id: str, room_id: str, event: dict) -> None:
        if event["content"]["msgtype"] != "m.text":
            print("\nUnsupported msg event:\n", json.dumps(event, indent=4))
            return

        sp = "&nbsp;"
        br = "<br>"

        if event["content"].get("format") == "org.matrix.custom.html":
            body = event["content"]["formatted_body"]
        else:
            body = event["content"]["body"].replace(" ", sp).replace("\n", br)

        if not body:
            return

        name  = self.get_user_displayname(room_id, event["sender"])
        color = "#00a5dc" if user_id == event["sender"] else "#d2236e"

        date = QDateTime.fromMSecsSinceEpoch(event["origin_server_ts"]).\
               toString("HH:mm:ss")

        msg = (f"<font color='{color}'>{name}</font>{sp}{sp}"
               f"<font color=gray><small>{date}</small></font>{br}"
               f"{body}")

        event["display"] = {"name": name, "date": time, "msg": msg}

        while True:
            try:
                queue = self.data[user_id][room_id]
                break
            except KeyError:
                time.sleep(0.1)

        queue.put((event["origin_server_ts"], event))


    @staticmethod
    def on_treat_error(err: Exception) -> None:
        raise err


    @staticmethod
    def get_user_displayname(room_id: str, user_id: str) -> str:
        try:
            room = main_window().accounts[user_id].rooms[room_id]
        except KeyError:
            pass
        else:
            name = room.members_displaynames.get(user_id)
            if name:
                return name

        for client in main_window().accounts.values():
            user = client.users.get(user_id)
            if user:
                return user.get_display_name()

        return user_id
