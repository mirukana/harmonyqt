# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from typing import Optional

from matrix_client.client import MatrixClient
from matrix_client.room import Room
from matrix_client.user import User
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (QHeaderView, QMainWindow, QSizePolicy,
                             QTreeWidget, QTreeWidgetItem,
                             QTreeWidgetItemIterator)

from . import __about__
from .caches import ROOM_DISPLAY_NAMES, USER_DISPLAY_NAMES
from .dialogs import AcceptRoomInvite


class UserTree(QTreeWidget):
    room_set_signal = pyqtSignal(MatrixClient, Room, bool)


    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.setColumnCount(2)  # avatar/name; indicator
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setAutoExpandDelay(500)
        self.setHeaderHidden(True)           # TODO: customizable cols
        self.setExpandsOnDoubleClick(False)  # double click = open page
        # self.setIndentation(0)
        # self.setSortingEnabled(True)

        self.header().setMinimumSectionSize(0)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.itemActivated.connect(self.on_row_click)
        self.room_set_signal.connect(self.expand_to_room)

        self.window.accounts.signal.login.connect(self.add_account)
        self.window.events.signal.room_name_change.connect(
            self.add_or_rename_room
        )


    def on_row_click(self, row: QTreeWidgetItem, _: int) -> None:
        if hasattr(row, "room"):
            client = row.parent().client

            if row.invite_by:
                dialog = AcceptRoomInvite(
                    client.user_id, row.text(0), row.invite_by.user_id
                )
                dialog.exec()
                clicked = dialog.clickedButton()

                if clicked is dialog.yes:
                    client.join_room(row.room.room_id)
                elif clicked is dialog.no:
                    try:
                        row.room.leave()
                    except KeyError:  # matrix_client bug
                        pass
                    return
                else:
                    return

            self.window.go_to_chat_dock(row.parent().client, row.room)


    @staticmethod
    def _find_row(parent, attr: Optional[str] = None, value = None
                 ) -> Optional[QTreeWidgetItem]:
        tree_iter = QTreeWidgetItemIterator(parent)

        while tree_iter.value():
            row = tree_iter.value()
            if not attr:
                return row
            if getattr(row, attr, None) == value:
                return row
            tree_iter += 1

        return None


    def add_account(self, client: MatrixClient) -> None:
        if self._find_row(self):   # If other account rows exists:
            QTreeWidgetItem(self)  # blank row separator

        row         = QTreeWidgetItem(self)
        row.client  = client
        row.user_id = client.user_id
        row.setText(0, f"• {USER_DISPLAY_NAMES.get(client)}")
        row.setToolTip(0, client.user_id)


    def add_or_rename_room(self,
                           client:    MatrixClient,
                           room:      Room,
                           invite_by: Optional[User] = None) -> None:

        if client.user_id not in self.window.accounts:
            raise ValueError(f"Account {client.user_id!r} not logged in.")

        texts   = [ROOM_DISPLAY_NAMES.get(room), ""]
        tooltip = "\n".join(room.aliases + [room.room_id])

        if invite_by:
            texts[1] = "?"
            tooltip = (
                f"Pending invitation from {USER_DISPLAY_NAMES.get(invite_by)} "
                f"({invite_by.user_id})\n{tooltip}"
            )

        account_row = None
        while not account_row:  # retry in case of slow login
            account_row = self._find_row(self, "client", client)
            time.sleep(0.05)

        rename   = True
        room_row = self._find_row(account_row, "room_id", room.room_id)
        if not room_row:
            room_row = QTreeWidgetItem(account_row)
            rename   = False

        room_row.room      = room
        room_row.room_id   = room.room_id
        room_row.invite_by = invite_by
        room_row.setTextAlignment(1, Qt.AlignRight)

        for col, txt in enumerate(texts):
            room_row.setText(col, txt)

        for col in range(self.columnCount()):
            room_row.setToolTip(col, tooltip)

        self.room_set_signal.emit(client, room, rename)


    def remove_room(self, client: MatrixClient, room: Room) -> None:
        try:
            account_row = self._find_row(self, "user_id", client.user_id)
            # comparing the "room" attr with room fails
            room_row    = self._find_row(account_row, "room_id", room.room_id)
            account_row.removeChild(room_row)
        except AttributeError:  # row not found
            pass


    # pylint: disable=unused-argument
    def expand_to_room(self, client: MatrixClient, room: Room, is_rename: bool
                      ) -> None:
        if is_rename:
            return

        self.expandToDepth(0)  # TODO: unless user collapsed manually


    # pylint: disable=invalid-name
    def sizeHint(self) -> QSize:
        cols = sum([self.columnWidth(c) for c in range(self.columnCount())])
        return QSize(max(cols, min(self.window.width() // 3, 360)), -1)
