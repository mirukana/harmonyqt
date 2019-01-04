# file Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from multiprocessing.pool import ThreadPool
from typing import Set

from PyQt5.QtCore import pyqtSignal

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room

from . import base
from .. import main_window


class InviteToRoom(base.GridDialog):
    invites_sent_signal = pyqtSignal()


    def __init__(self, room: Room, as_user: str = "") -> None:
        super().__init__()
        self.room  = room
        self._pool = ThreadPool(8)
        self.update_wintitle()

        us_in_room = {i for i in main_window().accounts if i in room.members}

        self.info_line = base.InfoLine(self)
        self.sender    = base.ComboBox(
            self,
            "Send invite as:",
            "Select the account that will be used to send this invite",
            items=sorted(us_in_room), initial_item=as_user
        )
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

        if as_user:
            self.invitees.text_edit.setFocus()

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

        self.invites_sent_signal.connect(self.on_invites_sent)
        main_window().events.signal.new_account.connect(self.on_new_login)
        main_window().events.signal.account_gone.connect(self.on_account_gone)
        main_window().events.signal.room_rename.connect(self.update_wintitle)


    def update_wintitle(self) -> None:
        self.setWindowTitle(
            f"Harmony - Invite to room: {self.room.display_name}"
        )


    def on_new_login(self, user_id: str) -> None:
        for member in self.room.get_joined_members():
            if member.user_id == user_id:
                self.creator.combo_box.addItem(user_id)


    def on_account_gone(self, user_id: str) -> None:
        self.sender.del_items_with_text(user_id)


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

        sent: Set[str] = set()

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


    def on_error(self, err: BaseException) -> None:
        # Without this handler, exceptions will be silently ignored
        if isinstance(err, MatrixRequestError):
            data = json.loads(err.content)
            self.info_line.set_err(data["error"])
        else:
            raise err


    def on_invites_sent(self) -> None:
        self.done(0)
