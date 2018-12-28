# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from . import register
from ..chat import Chat, markdown
from .utils import expand_user, str_arg_to_list


@register
def say(chat: Chat, text: str, with_accounts: str = "@") -> None:
    """Send message with any of your accounts connected to this room.
    `with_accounts` is a list of Matrix user IDs.
    If it is not specified (default), the user typing this command is used.

    Examples:

        /say "Same as sending a message normally"
        /say "Lorem ipsum" @test:matrix.org
        /say Hi! @,@alice:matrix.org,@test:matrix.org
    """
    for user_id in str_arg_to_list(with_accounts):
        chat = Chat(expand_user(chat, user_id), chat.room.room_id)
        send_markdown(chat, text)


def send_markdown(chat: Chat, text: str) -> None:
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    html = markdown.MARKDOWN.convert(text)
    chat.messages.local_echo(html)
    chat.room.send_html(html)
