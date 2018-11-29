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

        from . import messages, sendbox
        self.messages = messages.MessageList(self)
        self.sendbox  = sendbox.SendBox(self)

        self.vbox     = QVBoxLayout(self)
        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.sendbox)
