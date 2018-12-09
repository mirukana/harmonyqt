# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class Chat(QWidget):
    def __init__(self, window: QMainWindow, user_id: str, room_id: str
                ) -> None:
        super().__init__(window)
        self.window = window
        self.client = window.accounts[user_id]
        self.room   = self.client.rooms[room_id]

        self.vbox = QVBoxLayout(self)

        # layout_old_margin = self.vbox.contentsMargins()
        self.vbox.setContentsMargins(0, 0, 0, 0)

        from . import messages, send_area
        self.messages  = messages.MessageList(self)
        self.send_area = send_area.SendArea(self)

        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.send_area)
