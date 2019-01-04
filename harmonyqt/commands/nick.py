# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Optional

from . import register
from ..chat import Chat


@register
def nick(chat: Chat, args: dict) -> None:
    """Usage: /nick [NAME] [-r|--room]

    Set or clear display name, globally or only for this room.

    Options:
      -r, --room
        Set name only for the current room.

    Examples:
    ```
      /nick
      /nick Alice
      /nick "Not Alice" --room
    ```"""

    nick_f(chat=chat, name=args["NAME"], for_room=args["--room"])


def nick_f(chat: Chat, name: Optional[str] = None, for_room: bool = False
          ) -> None:
    if for_room:
        chat.room.set_user_profile(displayname=name or chat.client.user_id)
    else:
        chat.client.user.set_display_name(name or chat.client.user_id)
