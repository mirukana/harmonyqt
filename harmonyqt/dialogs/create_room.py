# file Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from multiprocessing.pool import ThreadPool

from matrix_client.client import MatrixClient
from matrix_client.room import Room
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QMainWindow

from . import base


class CreateRoom(base.GridDialog):
    room_created_signal = pyqtSignal(MatrixClient, Room)

    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window, "Create room")
        self._pool = ThreadPool(8)
        self.room_created_signal.connect(self.on_room_created)

        logged_in = sorted(self.main_window.accounts.keys())
        self.main_window.accounts.signal.login.connect(self.on_new_login)

        self.info_line = base.InfoLine(self)
        self.about     = QLabel(
            "All fields are optional.\n"
            "Room can be further customized after creation.",
            self
        )
        self.creator   = base.ComboBox(self, "Create with account:", logged_in)
        self.name      = base.Field(self, "Room name:")
        self.invitees  = base.Field(
            self,
            "Users to invite:",
            "@user1:server.tld @user2:matrix.org …",
            "",
            "Space-delimited list of users to invite to this room"
        )
        self.public = base.CheckBox(
            self,
            "&Make this room public",
            "Publish this room in the public room list; allow anyone to join."
        )
        self.federate = base.CheckBox(
            self,
            "&Allow users from different servers",
            ("User accounts from different homeservers than your account's "
             "will be able to join.\n"
             "These servers will get a copy of the room's history.\n"
             "This setting cannot be changed later."),
            check=True
        )
        self.create = base.AcceptButton(self, "&Create", self.validate)
        self.cancel = base.CancelButton(self, "Ca&ncel")

        blank = lambda: base.BlankLine(self)

        self.add_spacer(0, 0)
        self.add_spacer(0, 3)
        # widget, from row, from col, row span, col span, align = left
        self.grid.addWidget(self.info_line,  1,  1, 1, 2)
        self.grid.addWidget(self.about,      2,  1, 1, 2)
        self.grid.addWidget(blank(),         3,  1, 1, 2)
        self.grid.addWidget(self.creator,    4,  1, 1, 2)
        self.grid.addWidget(self.name,       5,  1, 1, 2)
        self.grid.addWidget(self.invitees,   7,  1, 1, 2)
        self.grid.addWidget(blank(),         8,  1, 1, 2)
        self.grid.addWidget(self.public,     9,  1, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(self.federate,   10, 1, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(blank(),         11, 1, 1, 2)
        self.grid.addWidget(self.create,     12, 1, 1, 1)
        self.grid.addWidget(self.cancel,     12, 2, 1, 1)
        self.add_spacer(13, 1)
        self.add_spacer(13, 3)

        for half_col in (1, 2):
            self.grid.setColumnMinimumWidth(half_col, 160)


    # TODO: handle disconnect
    def on_new_login(self, client: MatrixClient) -> None:
        while not hasattr(self, "creator"):
            time.sleep(0.05)

        self.creator.combo_box.addItem(client.user_id)


    def validate(self, _) -> None:
        self.info_line.set_info("Creating room...")

        creator  = self.creator.combo_box.currentText()
        name     = self.name.line_edit.text()
        invitees = self.invitees.line_edit.text().split()
        public   = self.public.isChecked()
        federate = self.federate.isChecked()

        if not creator:
            self.info_line.set_err("No creator account selected")
            return

        try:
            client = self.main_window.accounts[creator]
        except KeyError:
            self.info_line.set_err("Selected creator not connected")
            return

        def create() -> Room:
            # client.create_room doesn't have a federate param
            answer = client.api.create_room(
                name=name, is_public=public, invitees=invitees,
                federate=federate
            )
            # pylint: disable=protected-access
            room = client._mkroom(answer["room_id"])
            client.join_room(room.room_id)
            self.room_created_signal.emit(client, room)

        self._pool.apply_async(create)


    def on_room_created(self, client: MatrixClient, room: Room) -> None:
        self.done(0)
        self.main_window.go_to_chat_dock(client, room)
