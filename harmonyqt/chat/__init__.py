# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import functools

from matrix_client.client import MatrixClient
from matrix_client.room import Room
from matrix_client.user import User
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class Chat(QWidget):
    def __init__(self, room: Room, user: User, window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.room   = room
        self.user   = user

        from . import messages, sendbox
        self.messages = messages.MessageList(self)
        self.sendbox  = sendbox.SendBox(self)

        self.vbox     = QVBoxLayout(self)
        self.vbox.addWidget(self.messages)
        self.vbox.addWidget(self.sendbox)


@functools.lru_cache(64)
def get_cached_user(client: MatrixClient, user_id: str) -> User:
    # TODO: drop user if important detail changes
    return User(client, user_id)
