# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from cachetools import LFUCache
from kids.cache import cache
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from .. import dock, main_window, register_startup_function
from ..message import Message


class ChatDock(dock.Dock):
    def __init__(self, user_id: str, room_id: str, parent: QWidget) -> None:
        self.user_id: str = user_id
        self.room_id: str = room_id
        super().__init__(self.title, parent, can_hide_title_bar=False)
        self.change_room(self.user_id, self.room_id)

        self.visibilityChanged.connect(self.on_visibility_change)
        self.dockLocationChanged.connect(self.on_location_change)


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
        main_window().visible_chat_docks.pop((self.user_id, self.room_id),
                                             None)

        self.user_id, self.room_id = to_user_id, to_room_id
        self.chat = Chat(self.user_id, self.room_id)
        self.setWidget(self.chat)
        self.update_title()

        main_window().visible_chat_docks[(self.user_id, self.room_id)] = self


    def focus(self) -> None:
        super().focus()
        self.chat.send_area.box.setFocus()


    def on_visibility_change(self, visible: bool) -> None:
        ids = (self.user_id, self.room_id)
        if visible:
            main_window().visible_chat_docks[ids] = self
        else:
            main_window().visible_chat_docks.pop(ids, None)


    def on_location_change(self, _: Qt.AllDockWidgetAreas) -> None:
        # Needed for situations where user drags a dock then opens a new
        # chat, since the location of that new chat dock is dependent on
        # the last focused dock.
        self.focus()


@cache(use=LFUCache(maxsize=64))
class Chat(QWidget):
    def __init__(self, user_id: str, room_id: str) -> None:
        super().__init__()

        self.client = main_window().accounts[user_id]
        self.room   = self.client.rooms[room_id]

        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        from . import messages, send_area
        self.messages  = messages.MessageList(self)
        self.send_area = send_area.SendArea(self)

        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.send_area)


def redirect_message(msg: Message) -> None:
    if msg.receiver_id is None:  # local echo
        return

    chat = Chat(msg.receiver_id, msg.room_id)  # cache
    chat.messages.on_receive_from_server(msg)


register_startup_function(
    lambda _, win: win.events.signal.new_message.connect(redirect_message)
)
