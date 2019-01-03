# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading

from . import register, utils
from ..chat import Chat
from ..message import Message

SEND_LOCK = threading.Lock()


@register
def say(chat: Chat, args: dict) -> None:
    """Usage: /say MESSAGES... [-h|--html -e|--echo]

    Print/send markdown or HTML messages.

    Options:
      -h, --html
        Parse `MESSAGES` as HTML instead of markdown.

      -e, --echo
        Print `MESSAGES` locally without sending them.

    Examples:
    ```
      /say "Same as sending a message without using a command"
      /say "**Bold message 1**" "*Italic message 2*"
      /say "<a href='https://example.com'>Example link</a>" --html
      /say "Talking to myself" --echo
    ```"""

    for msg in args["MESSAGES"]:
        say_f(chat=chat, text=msg, is_html=args["--html"], echo=args["--echo"])


def say_f(chat: Chat, text: str, is_html: bool = False, echo: bool = False
         ) -> None:
    if not text.strip():
        return

    if echo:
        utils.print_info(chat, text, is_html=is_html)
        return


    msg = Message(
        sender_id = chat.client.user_id,
        room_id   = chat.room.room_id,
        markdown  = text if not is_html else "",
        html      = text if is_html     else "",
    )

    # Prevent mixing up if user sends msg B before msg A is received
    # by the server:
    with SEND_LOCK:
        msg.send()
