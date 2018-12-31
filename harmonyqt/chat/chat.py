# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from cachetools import LFUCache
from kids.cache import cache
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from .. import main_window, message, register_startup_function


@cache(use=LFUCache(maxsize=64))
class Chat(QWidget):
    def __init__(self, user_id: str, room_id: str) -> None:
        super().__init__()

        self.client = main_window().accounts[user_id]
        self.room   = self.client.rooms[room_id]

        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        # Because of circular import
        from .message_display import MessageDisplay
        from .send_area import SendArea
        self.messages  = MessageDisplay(self)
        self.send_area = SendArea(self)

        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.send_area)

        from .shortcuts import get_shortcuts
        self.shortcuts = list(get_shortcuts(self))


def redirect_message(msg: message.Message) -> None:
    if msg.receiver_id is None:  # local echo
        return

    chat = Chat(msg.receiver_id, msg.room_id)  # cache
    chat.messages.on_receive_from_server(msg)


register_startup_function(
    lambda _, win: win.events.signal.new_message.connect(redirect_message)
)
