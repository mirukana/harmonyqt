# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading

from . import register, utils
from ..chat import Chat
from ..message import Message


@register
def say(chat: Chat, args: dict) -> None:
    """
    Usage:
      /devices [USER_ID]
               [DEVICES_ID...
                [-v|--verify | -b|--blacklist | -i|--ignore | --delete]]

    List, (un)trust or delete user devices.

    If `USER_ID` is unspecified, your current user is used.
    If no `DEVICES_ID` is specified, your/`USER_ID`'s devices will be listed.
    Options will apply to the specified `DEVICES_ID`.

    To verify that one of your device can be trusted:
      - From that device, check its name, ID and key by e.g.
        typing `/devices` from Harmony or going to User Settings in Riot
      - Ensure that these match with what you see by typing `/devices` here.

    To verify that someone else's device can be trusted:
      - Ask the owner for the device's name, ID and key they see
      - Ensure that these match with what you see by typing `/devices` here.

    Devices that you don't recognize or that fails the check above
    could be attackers eavesdropping and should be blacklisted.

    Options:
      -t, --trust
        Mark `DEVICES_ID` as verified.
        In encrypted rooms, messages are by default only sent to your and
        other users's verified devices.

      -b, --blacklist
        Mark `DEVICES_ID` as blacklisted.
        In encrypted rooms, messages will never be sent to these devices.

      -i, --ignore
        Allow sending encrypted messages to `DEVICES_ID` regardless of
        if they are untrusted.

    Examples:
    ```
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
