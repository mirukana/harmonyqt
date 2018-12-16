# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from collections import UserDict
from multiprocessing.pool import ThreadPool
from queue import PriorityQueue
from typing import Dict

from dataclasses import dataclass, field
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime

from . import main_window
from .chat import markdown

DATE_FORMAT = "HH:mm:ss"


class MessageProcessor(UserDict):
    def __init__(self) -> None:
        super().__init__()
        # Dicts structure: {receiver_id: {room_id: Queue}} - FIXME: mypy crash
        self.data:  Dict[str, Dict[str, PriorityQueue]] = {}  # type: ignore
        self._pool: ThreadPool                          = ThreadPool(8)

        main_window().events.signal.new_message.connect(self.on_new_message)


    def on_new_message(self, receiver_id: str, event: dict) -> None:
        self._pool.apply_async(self.queue_event, (receiver_id, event),
                               error_callback = self.on_queue_event_error)


    def queue_event(self, receiver_id: str, event: dict) -> None:
        ev = event
        try:
            if ev["content"]["msgtype"] != "m.text":
                raise RuntimeError
        except Exception:
            print("\nUnsupported msg event:\n", json.dumps(ev, indent=4))
            return

        if ev["content"].get("format") == "org.matrix.custom.html":
            content = ev["content"]["formatted_body"]
        else:
            content = markdown.MARKDOWN.convert(ev["content"]["body"])

        timestamp = int(ev["origin_server_ts"])
        msg       = Message(ev["sender"], receiver_id, ev["room_id"],
                            content, timestamp)

        if receiver_id not in self.data:
            self.data[receiver_id] = {}

        if ev["room_id"] not in self.data[receiver_id]:
            self.data[receiver_id][ev["room_id"]] = PriorityQueue()

        queue = self.data[receiver_id][ev["room_id"]]
        queue.put((-timestamp, msg))


    @staticmethod
    def on_queue_event_error(err: BaseException) -> None:
        raise err


@dataclass
class Message:
    sender_id:   str = ""
    receiver_id: str = ""
    room_id:     str = ""
    content:     str = ""
    # If 0, timestamp = now
    ms_since_epoch: int = 0
    # If empty, use the default avatar icon
    avatar_url: str = ""

    html_avatar:  str = field(init=False, default="")
    html_info:    str = field(init=False, default="")
    html_content: str = field(init=False, default="")


    def __post_init__(self) -> None:
        assert bool(self.sender_id and self.receiver_id and self.room_id and
                    self.content)


        cl = " message"
        cl = f" {cl} own-message" if self.sender_id == self.receiver_id else cl

        self.html_content = f"<p class='content{cl}'>{self.content}</p>"

        self.html_avatar = "<p class='avatar%s'><img src='%s'></p>" % (
            cl,
            self.avatar_url or main_window().icons.path("default_avatar_small")
        )

        if not self.ms_since_epoch:
            self.ms_since_epoch = \
                    QDateTime.currentDateTime().toMSecsSinceEpoch()

        date = QDateTime.fromMSecsSinceEpoch(self.ms_since_epoch)\
               .toString(DATE_FORMAT)


        self.html_info = (
            f"<p class='info{cl}'>"
            f"<span class='name'>{self.user_display_name}</span>&nbsp;"
            f"<span class='date'>{date}</span>"
            f"</p>"
        )


    def was_created_before(self, ms_since_epoch: int) -> bool:
        return self.ms_since_epoch < ms_since_epoch


    @property
    def user_display_name(self) -> str:
        try:
            room = main_window().accounts[self.sender_id].rooms[self.room_id]
        except KeyError:
            pass
        else:
            name = room.members_displaynames.get(self.sender_id)
            if name:
                return name

        for client in main_window().accounts.values():
            user = client.users.get(self.sender_id)
            if user:
                return user.get_display_name()

        return self.sender_id
