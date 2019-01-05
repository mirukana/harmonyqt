# file Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from multiprocessing.pool import ThreadPool

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel

from matrix_client.errors import MatrixRequestError

from . import base
from .. import main_window


class CreateRoom(base.GridDialog):
    # User ID, Room ID
    room_created_signal = pyqtSignal(str, str)

    def __init__(self, for_user_id: str = "") -> None:
        super().__init__("Create room")
        self._pool = ThreadPool(8)
        self.room_created_signal.connect(self.on_room_created)

        logged_in = sorted(main_window().accounts.keys())

        self.info_line = base.InfoLine(self)
        self.about     = QLabel(
            "All fields are optional.<br>"
            "Room can be further customized after creation.<br>"
            "<i>Settings with a * cannot be changed later.</i>",
            self
        )
        self.about.setTextFormat(Qt.RichText)
        self.creator   = base.ComboBox(
            self,
            "Create with account:",
            "Select the account that will be the administrator of this room",
            items=logged_in, initial_item=for_user_id
        )
        self.name      = base.Field(self, "Room name:")
        self.invitees  = base.Field(
            self,
            "Users to invite:",
            "@user1:server.tld\n@user2:matrix.org\n…",
            "",
            "Whitespace-delimited list of user IDs to invite in this room",
            lines = 3
        )
        self.public = base.CheckBox(
            self,
            "&Make this room public",
            "Publish this room in the public room list; allow anyone to join."
        )
        self.federate = base.CheckBox(
            self,
            "&Allow users from different servers*",
            ("User accounts from different homeservers than your account's "
             "will be able to join.\n"
             "These servers will get a copy of the room's history.\n"
             "This setting cannot be changed later."),
            check=True
        )
        self.create = base.AcceptButton(self, "&Create", self.validate)
        self.cancel = base.CancelButton(self, "Ca&ncel")

        if for_user_id:
            self.name.text_edit.setFocus()

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

        main_window().events.signals.new_account.connect(self.on_new_account)
        main_window().events.signals.account_gone.connect(self.on_account_gone)


    def on_new_account(self, user_id: str) -> None:
        self.creator.combo_box.addItem(user_id)


    def on_account_gone(self, user_id: str) -> None:
        self.creator.del_items_with_text(user_id)


    def validate(self, _) -> None:
        self.info_line.set_info("Creating room...")

        creator  = self.creator.combo_box.currentText()
        name     = self.name.get_text()
        invitees = [t.strip() for t in self.invitees.get_text().split()
                    if t.strip()]
        public   = self.public.isChecked()
        federate = self.federate.isChecked()

        if not creator:
            self.info_line.set_err("No creator account selected")
            return

        try:
            client = main_window().accounts[creator]
        except KeyError:
            self.info_line.set_err("Selected creator not connected")
            return

        def create() -> None:
            # client.create_room doesn't have a federate param
            answer = client.api.create_room(
                name=name, is_public=public, invitees=invitees,
                federate=federate
            )
            # pylint: disable=protected-access
            room = client._mkroom(answer["room_id"])
            client.join_room(room.room_id)
            self.room_created_signal.emit(client.user_id, room.room_id)

        self._pool.apply_async(create, error_callback=self.on_error)


    def on_error(self, err: BaseException) -> None:
        # Without this handler, exceptions will be silently ignored
        if isinstance(err, MatrixRequestError):
            data = json.loads(err.content)
            self.info_line.set_err(data["error"].replace("user_id", "user ID"))
        else:
            raise err


    def on_room_created(self, user_id: str, room_id: str) -> None:
        self.done(0)
        main_window().go_to_chat_dock(user_id, room_id)
