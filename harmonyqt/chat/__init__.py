# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from matrix_client.client import MatrixClient
from matrix_client.room import Room
from matrix_client.user import User
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class Chat(QWidget):
    def __init__(self, window: QMainWindow, client: MatrixClient, room: Room
                ) -> None:
        super().__init__(window)
        self.window = window
        self.client = client
        self.room   = room

        self.vbox = QVBoxLayout(self)

        # layout_old_margin = self.vbox.contentsMargins()
        self.vbox.setContentsMargins(0, 0, 0, 0)

        from . import messages, send_area
        self.messages  = messages.MessageList(self)
        self.send_area = send_area.SendArea(self)

        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.send_area)
