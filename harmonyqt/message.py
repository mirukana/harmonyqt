# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
from copy import copy
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple

from dataclasses import dataclass
from PyQt5.QtCore import QDateTime

from . import main_window, markdown

DATE_FORMAT = "HH:mm:ss"


@dataclass
class Message:
    """Represents a locally generated or received from server message.

    Class variables:
        local_echo_hooks:
            Dict of `identifier: functions` that will receive Message objects
            to [locally echo](https://tinyurl.com/matrix-local-echo)
            when Message.send() is called.
            Identifier can be a string or any other object.

    Attributes:
        room_id:
            ID of the room this message belongs to, required.

        sender_id:
            Matrix user ID of the message's sender, required.

        receiver_id:
            Matrix user ID of the account that received this message.
            If `None` (default), message is assumed to be locally generated.

        markdown:
            Content of the message in plain text/markdown format.
            If not specified, `html` must be and is converted to `markdown`.

        html:
            Content of the message in HTML format.
            If not specified, `markdown` must be and is converted to `html`.

        ms_since_epoch:
            Unix timestamp in microseconds for the message's creation.
            If not specified, the current time will be used.

        avatar_url:
            HTTP(s) URL of the sender's avatar, if he has one."""

    # Can't define a pyqtSignal(this_class) here
    local_echo_hooks: ClassVar[Dict[Any, Callable[["Message"], None]]] = {}

    room_id:     str           = ""
    sender_id:   str           = ""
    receiver_id: Optional[str] = None
    markdown:    str           = ""
    html:        str           = ""
    # If 0, timestamp = now
    ms_since_epoch: int = 0
    # If empty, use the default avatar icon
    avatar_url: Optional[str] = None


    def __post_init__(self) -> None:
        assert bool(self.sender_id), "No sender_id argument passed."
        assert bool(self.room_id),   "No room_id argument passed."

        if self.markdown and not self.html:
            self.html = markdown.to_html(self.markdown)

        elif self.html and not self.markdown:
            self.markdown = markdown.from_html(self.html)

        elif not self.html and not self.markdown:
            raise TypeError("No markdown or html argument passed.")

        self.linkify_in_html()

        self.ms_since_epoch = self.ms_since_epoch or \
                              QDateTime.currentDateTime().toMSecsSinceEpoch()


    @property
    def _html_class(self) -> str:
        return "message own-message" \
               if self.sender_id == self.receiver_id else "message"

    @property
    def html_avatar(self) -> str:
        "HTML to be displayed by a widget for avatar."

        return ""
        # return "<div class='avatar%s'><img src='%s'></div>" % (
            # self._html_class,
          # self.avatar_url or main_window().icons.path("default_avatar_small")
        # )

    @property
    def html_info(self) -> str:
        "HTML to be displayed by a widget for the info line (name, date, ...)."

        date = QDateTime.fromMSecsSinceEpoch(self.ms_since_epoch)\
               .toString(DATE_FORMAT)

        return (
            f"<div class='info {self._html_class}'>"
            f"<span class='name'>{self.sender_display_name}</span>&nbsp;"
            f"<span class='date'>{date}</span>"
            f"</div>"
        )

    @property
    def html_content(self) -> str:
        "HTML to be displayed by a widget for the message's content."

        return f"<div class='content {self._html_class}'>{self.html}</div>"


    def was_created_before(self, ms_since_epoch: int) -> bool:
        """Return if this message was created before `ms_since_epoch`,
        a unix timestamp in microseconds."""

        return self.ms_since_epoch < ms_since_epoch


    @property
    def sender_display_name(self) -> str:
        "Display name for `self.sender_id`. Tries to avoid network requests."

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


    def linkify_in_html(self) -> None:
        "Wrap all `self.html` URLs in <a> tags if they aren't already."

        html = self.html

        def replacer(match) -> str:
            url = [g for g in match.groups() if g is not None][0]

            re_localhost = r"(?:127\.0\.0\.1|localhost)(?::\d+)?"

            href = "%s%s" % (
                ""        if "://" in url else
                "mailto:" if re.match(r"[^@]+@[^@]+", url) else
                "http://" if re.match(re_localhost, url) else
                "https://",
                url
            )

            for already_linkified in a_tags:
                if href in already_linkified:
                    return url

            return f"<a href='{href}'>{url}</a>"

        # List of <a> tags and anything inside them: `<a …> … <a/ …>`
        a_tags = re.findall(r"<\s*?a(?:\s+\S+)?>[^<]*<\s*/?\s*a(?:\s+\S+)?>",
                            html)

        # Match URL/domains in html like `scheme://…`, `….tld` or `….tld:80/…',
        # IPs and mail addresses:
        reu = (
            r"[A-Za-z]+:///?[^\s<]+|"
            r"(?:[\w_-][\w@._-]*[\w_-]\.[A-Za-z]{2,9}|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"localhost)(?::\d+)?(?:/[^\s<]+)?"
        )

        # Allow URL/domain captures between these characters:
        pairs: List[Tuple[str, str]] = [
            # Begin/end of line, whitespace or HTML tags end/begin
            (r"(?<=^)|(?<=\s)|(?<=>)", r"(?:$|\s|<)"),
            ("<", ">"),
            ("&lt;", "&gt;"),
            ("&gt;", "&lt;"),
            (r"\(", r"\)"),
            (r"\[", r"\]"),
            (r"\{", r"\}"),
        ]

        final_regex = r"(?:%s)" % r"|".join(
            (rf"(?<={p[0]})({reu})(?={p[1]})" for p in pairs)
        )
        self.html = re.sub(final_regex, replacer, html)


    def send(self) -> None:
        "Send this message to the room specified by `self.room_id`."

        room = main_window().accounts[self.sender_id].rooms[self.room_id]
        for func in self.local_echo_hooks.values():
            func(copy(self))
        room.send_html(html=self.html, body=self.markdown)
