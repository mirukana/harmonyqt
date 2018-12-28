# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from . import register
from ..chat import Chat
from .utils import expand_user


@register
def nick(chat: Chat, name: str = "", only_for_room: str = "no", user: str = "@"
        ) -> None:
    """Set or clear display name, globally or only for this room.
    If `name` is empty, your display name will be unset.
    The user ID of an account you are logged to can be specified as `user`.
    If unspecified (default), the user typing this command is used.

    Examples:

        /nick Alice
        /nick "Not Alice" only_for_room=yes
        /nick ""
        /nick "" yes
    """
    user_id = expand_user(chat, user)
    chat    = Chat(user_id, chat.room.room_id)
    if only_for_room:
        chat.room.set_user_profile(displayname=name or user_id)
    else:
        chat.client.h_user.set_displayname(name or user_id)
