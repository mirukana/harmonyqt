# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from typing import Any, Callable, Dict

from matrix_client.client import MatrixClient
from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room

from . import register, utils
from ..chat import Chat

SETTINGS_FUNC: Dict[str, Callable[[MatrixClient, Room, Any], bool]] = {
    "name":          lambda c, r, v: r.set_room_name(v),
    "topic":         lambda c, r, v: r.set_room_topic(v),
    "alias_add":     lambda c, r, v: c.api.set_room_alias(r.room_id, v),
    "alias_del":     lambda c, r, v: c.api.remove_room_alias(v),
    "allow_guests":  lambda c, r, v: r.set_guest_access(True),
    "refuse_guests": lambda c, r, v: r.set_guest_access(False),
    "public":        lambda c, r, v: r.set_invite_only(False),
    "private":       lambda c, r, v: r.set_invite_only(True),
    "enable_e2e":    lambda c, r, v: r.enable_encryption(),
}


@register
def room_set(chat: Chat, args: dict) -> None:
    """Usage: /room_set [options]

    Change settings for the current room (see `/help room_set`).

    Options:
      -n NAME, --name NAME
        Set this room's display name.

      -t TOPIC, --topic TOPIC
        Set this room's description.

      -a ALIAS, --alias-add ALIAS
        Add an #alias for this room.
        If the room is public, users can join it easily using an alias.

      -A ALIAS, --alias-del ALIAS
        Remove a previously set #alias for this room.

      -g, --allow-guests
        Allow guests (unregistered accounts) to join this room.

      -G, --refuse-guests
        Prevent guests from joining this room.

      -p, --public
        Anyone can join this room if they know its ID, link or alias.

      -P, --private
        Require an invitation to join this room.

      --enable-e2e
        Enable end-to-end encryption for this room. Be warned:
        - Once enabled in a room, it can never be disabled again
        - Encryption is still in development
        - New users/devices will not be able to read the room's history from
          before they joined
        - Encrypted messages will only be visible to clients that supports it,
          e.g. Riot and Harmony.

    Examples:
    ```
      /room_set -n "Test room" -t "Just a test"
      /room_set --refuse-guests --private --enable-e2e
    ```"""

    for arg, val in args.items():
        if arg[2:].replace("-", "_") not in SETTINGS_FUNC:
            utils.print_err(chat, f"Unknown setting: {arg!r}.")
            return

    one_passed = False

    for arg, val in args.items():
        if not (val is True or isinstance(val, str)):
            continue

        one_passed = True

        func_name = arg[2:].replace("-", "_")

        try:
            result = SETTINGS_FUNC[func_name](chat.client, chat.room, val)
        except MatrixRequestError as err:
            data = json.loads(err.content)
            utils.print_err(chat, data["error"].replace("don't", "do not"))
        else:
            if result is False:
                utils.print_err(
                    chat,
                    f"You do not have permission to set `{arg}` in this room"
                )

    if not one_passed:
        utils.print_warn(chat, "No option passed, see `/help room_set`.")
