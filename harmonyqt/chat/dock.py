# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from multiprocessing.pool import ThreadPool

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from . import Chat
from .. import dock, main_window


class ChatDock(dock.Dock):
    def __init__(self, user_id: str, room_id: str, parent: QWidget) -> None:
        self.user_id: str = user_id
        self.room_id: str = room_id
        super().__init__(f"{self.user_id}: {self.room_id}",
                         parent=parent, can_hide_title_bar=False)

        self._pool = ThreadPool(1)
        self.autoset_title()

        self.change_room(self.user_id, self.room_id)

        self.visibilityChanged.connect(self.on_visibility_change)
        self.dockLocationChanged.connect(self.on_location_change)


    def autoset_title(self) -> None:
        def get() -> str:
            client = main_window().accounts[self.user_id]
            return ": ".join((client.user.get_display_name(),
                              client.rooms[self.room_id].display_name))

        def set_(title: str) -> None:
            self.title = title

        self._pool.apply_async(get, callback=set_)


    def change_room(self, to_user_id: str, to_room_id: str) -> None:
        main_window().visible_chat_docks.pop((self.user_id, self.room_id),
                                             None)

        self.user_id, self.room_id = to_user_id, to_room_id
        self.chat = Chat(self.user_id, self.room_id)
        self.setWidget(self.chat)
        self.autoset_title()

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
