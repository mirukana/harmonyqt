# file Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import time
from multiprocessing.pool import ThreadPool

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room
# pylint: disable=no-name-in-module
from PyQt5.QtCore import pyqtSignal

from . import base
from .. import main_window


class InviteToRoom(base.GridDialog):
    invites_sent_signal = pyqtSignal()


    def __init__(self, room: Room) -> None:
        # TODO: conn rename
        super().__init__(f"Invite to room: {room.display_name}")
        self.room  = room
        self._pool = ThreadPool(8)
        self.invites_sent_signal.connect(self.on_invites_sent)

        room_uids  = {m.user_id for m in room.get_joined_members()}
        us_in_room = {i for i in main_window().accounts if i in room_uids}
        main_window().events.signal.new_account.connect(self.on_new_login)

        self.info_line = base.InfoLine(self)
        self.sender    = base.ComboBox(self, "Send invite as:",
                                       items=sorted(us_in_room))
        self.invitees  = base.Field(
            self,
            "Users to invite:",
            "@user1:server.tld\n@user2:matrix.org\n…",
            "",
            "Whitespace-delimited list of user IDs to invite in this room",
            lines = 9
        )
        self.send   = base.AcceptButton(self, "&Send", self.validate)
        self.cancel = base.CancelButton(self, "&Cancel")

        blank = lambda: base.BlankLine(self)

        self.add_spacer(0, 0)
        self.add_spacer(0, 3)
        # widget, from row, from col, row span, col span, align = left
        self.grid.addWidget(self.info_line,  1, 1, 1, 2)
        self.grid.addWidget(self.sender,     2, 1, 1, 2)
        self.grid.addWidget(self.invitees,   3, 1, 1, 2)
        self.grid.addWidget(blank(),         4, 1, 1, 2)
        self.grid.addWidget(self.send,       5, 1, 1, 1)
        self.grid.addWidget(self.cancel,     5, 2, 1, 1)
        self.add_spacer(6, 1)
        self.add_spacer(6, 3)

        for half_col in (1, 2):
            self.grid.setColumnMinimumWidth(half_col, 160)


    # TODO: handle disconnect
    def on_new_login(self, user_id: str) -> None:
        while not hasattr(self, "sender"):
            time.sleep(0.05)

        for member in self.room.get_joined_members():
            if member.user_id == user_id:
                self.creator.combo_box.addItem(user_id)


    def validate(self, _) -> None:
        self.info_line.set_info("Sending invites...")

        sender   = self.sender.combo_box.currentText()
        invitees = self.invitees.get_text().split()

        if not sender:
            self.info_line.set_err("No sender account selected")
            return

        try:
            client = main_window().accounts[sender]
        except KeyError:
            self.info_line.set_err("Selected sender not connected")
            return

        sent = set()

        def send(to_user_id: str) -> None:
            # If user gets an error, edit the invitees and click "Send" again:
            if to_user_id in sent:
                return
            # client.invite_user won't let us handle errors
            client.api.invite_user(self.room.room_id, to_user_id)
            sent.add(to_user_id)

        def done(_) -> None:
            self.invites_sent_signal.emit()

        self._pool.map_async(send, invitees,
                             callback=done, error_callback=self.on_error)


    def on_error(self, err: Exception) -> None:
        # Without this handler, exceptions will be silently ignored
        if isinstance(err, MatrixRequestError):
            data = json.loads(err.content)
            self.info_line.set_err(data["error"])
        else:
            raise err


    def on_invites_sent(self) -> None:
        self.done(0)
