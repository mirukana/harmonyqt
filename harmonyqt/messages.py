# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import re
from collections import UserDict
from multiprocessing.pool import ThreadPool
from queue import PriorityQueue
from typing import Dict, Set

from dataclasses import dataclass, field
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime

from . import main_window
from .chat import markdown

DATE_FORMAT = "HH:mm:ss"

MESSAGE_FILTERS: Dict[str, str] = {
    # Qt only knows <s> for striketrough
    r"(</?)\s*(del|strike)>": r"\1s>",
}


class MessageProcessor(UserDict):
    def __init__(self) -> None:
        super().__init__()
        # Dicts structure: {receiver_id: {room_id: Queue}} - FIXME: mypy crash
        self.data:  Dict[str, Dict[str, PriorityQueue]] = {}  # type: ignore
        self._pool: ThreadPool                          = ThreadPool(8)

        self.received_event_ids: Set[str] = set()

        main_window().events.signal.new_message.connect(self.on_new_message)


    def on_new_message(self, receiver_id: str, event: dict) -> None:
        if event["event_id"] in self.received_event_ids:
            return

        self._pool.apply_async(self._queue_event, (receiver_id, event),
                               error_callback = self.on_queue_event_error)
        self.received_event_ids.add(event["event_id"])


    def _queue_event(self, receiver_id: str, event: dict) -> None:
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
        self.filter_content()
        self.content_linkify_in_html()

        cl = " message"
        cl = f" {cl} own-message" if self.sender_id == self.receiver_id else cl

        self.html_content = f"<div class='content{cl}'>{self.content}</div>"

        self.html_avatar = "<div class='avatar%s'><img src='%s'></div>" % (
            cl,
            self.avatar_url or main_window().icons.path("default_avatar_small")
        )

        if not self.ms_since_epoch:
            self.ms_since_epoch = \
                    QDateTime.currentDateTime().toMSecsSinceEpoch()

        date = QDateTime.fromMSecsSinceEpoch(self.ms_since_epoch)\
               .toString(DATE_FORMAT)


        self.html_info = (
            f"<div class='info{cl}'>"
            f"<span class='name'>{self.user_display_name}</span>&nbsp;"
            f"<span class='date'>{date}</span>"
            f"</div>"
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


    def filter_content(self) -> None:  # content: HTML
        content = self.content
        for regex, repl in MESSAGE_FILTERS.items():
            content = re.sub(regex, repl, content, re.IGNORECASE, re.MULTILINE)
        self.content = content


    def content_linkify_in_html(self) -> None:
        content = self.content

        def repl(match) -> str:
            url: str = match.group()

            href = re.sub(r"(^<|<$|^>|>$|^\(|\)$)", "", url)
            href = f"http://{url}" if "://" not in href else href

            for already_linkified in a_tags:
                if href in already_linkified:
                    return url

            link = f"<a href='{href}'>{url}</a>"

            # Make <links> work properly, sanitize < >
            link = re.sub(rf"^(<a href='.+'>)<(.+)", r"&lt;\1\2", link)
            link = re.sub(rf"^(<a href='.+'>)>(.+)", r"&gt;\1\2", link)
            link = re.sub(rf"<</a>$",                r"</a>&lt;", link)
            link = re.sub(rf"></a>$",                r"</a>&gt;", link)
            return link

        # List of <a> tags and anything inside them: `<a …> … <a/ …>`
        a_tags = re.findall(r"<\s*?a(?:\s+\S+)?>[^<]*<\s*/?\s*a(?:\s+\S+)?>",
                            content)

        # List of URLs found in content like `https://thing` or `example.com`
        self.content = re.sub(
            r"<?\(?([A-Za-z]+:///?[^\s<]+|"                    # scheme://…
            r"[\w\d\._-]+\.[A-Za-z]{2,9}(?:/[^\s<]+)?)>?\)?",  # ….tld ….tld/…

            repl, content
        )
