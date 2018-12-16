# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from cachetools import LFUCache
from kids.cache import cache
# pylint: disable=no-name-in-module
from PyQt5.QtGui import QFocusEvent
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from .. import dock, main_window


class ChatDock(dock.Dock):
    def __init__(self, user_id: str, room_id: str, parent: QWidget,
                 title_bar: bool = False) -> None:
        self.user_id: str = user_id
        self.room_id: str = room_id
        super().__init__(self.title, parent, title_bar)
        self.change_room(self.user_id, self.room_id)

        # When e.g. user select the tab for this dock
        self.visibilityChanged.connect(self.on_visibility_change)


    @property
    def title(self) -> str:
        client = main_window().accounts[self.user_id]
        return ": ".join((
            client.h_user.get_display_name(),
            client.rooms[self.room_id].display_name
        ))


    def update_title(self) -> None:
        self.setWindowTitle(self.title)


    def change_room(self, to_user_id: str, to_room_id: str) -> None:
        self.chat = Chat(to_user_id, to_room_id)
        self.user_id, self.room_id = to_user_id, to_room_id
        self.setWidget(self.chat)
        self.update_title()


    def focus(self) -> None:
        super().focus()
        self.chat.send_area.box.setFocus()


    def on_visibility_change(self, visible: bool) -> None:
        if visible:
            self.focus()


@cache(use=LFUCache(maxsize=12))
class Chat(QWidget):
    def __init__(self, user_id: str, room_id: str) -> None:
        super().__init__()
        self.client = main_window().accounts[user_id]
        self.room   = self.client.rooms[room_id]

        self.vbox = QVBoxLayout(self)

        # layout_old_margin = self.vbox.contentsMargins()
        self.vbox.setContentsMargins(0, 0, 0, 0)

        from . import messages, send_area
        self.messages  = messages.MessageList(self)
        self.send_area = send_area.SendArea(self)

        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.send_area)
