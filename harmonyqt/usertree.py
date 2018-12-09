# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Dict, List, Optional

from matrix_client.client import MatrixClient
from matrix_client.room import Room
from matrix_client.user import User
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QHeaderView, QMainWindow, QSizePolicy,
                             QTreeWidget, QTreeWidgetItem)

from . import __about__, actions
from .caches import ROOM_DISPLAY_NAMES, USER_DISPLAY_NAMES
from .dialogs import AcceptRoomInvite
from .menu import Menu


class UserTree(QTreeWidget):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self.window   = window
        self.accounts:   Dict[str, "AccountRow"] = {}
        self.blank_rows: List["BlankRow"]        = []

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setColumnCount(2)  # avatar/name; unread msg num/invite indicator
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setAutoExpandDelay(500)
        self.setHeaderHidden(True)  # TODO: customizable cols
        # self.setIndentation(0)
        # self.setSortingEnabled(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

        self.header().setMinimumSectionSize(0)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu_request)
        self.itemActivated.connect(self.on_row_activation)

        self.window.accounts.signal.login.connect(self.add_account)
        event_sig = self.window.events.signal
        event_sig.new_room.connect(self.on_add_room)
        event_sig.new_invite.connect(self.on_add_room)
        event_sig.room_rename.connect(self.on_rename_room)
        event_sig.left_room.connect(self.on_left_room)


    def add_account(self, client: MatrixClient) -> None:
        self.accounts[client.user_id] = AccountRow(self, client)

        root = self.invisibleRootItem()
        root.sortChildren(0, Qt.AscendingOrder)

        for row in self.blank_rows:
            root.removeChild(row)

        for row in self.accounts.values():
            index = root.indexOfChild(row)
            if index > 0:
                blank = BlankRow()  # Don't define a parent here!
                root.insertChild(index, blank)
                self.blank_rows.append(blank)


    def on_row_activation(self, row: QTreeWidgetItem, _: int) -> None:
        if hasattr(row, "on_activation"):
            row.on_activation()
            self.really_clear_selection()


    def on_context_menu_request(self, position: QPoint) -> None:
        selected = [self.itemFromIndex(s) for s in self.selectedIndexes()
                    if s.column() == 0]

        acts = []
        for row in selected:
            if hasattr(row, "get_context_menu_actions"):
                acts += row.get_context_menu_actions()

        menu = Menu(self, acts)
        menu.exec_(self.mapToGlobal(position))


    def on_add_room(self, client: MatrixClient, room: Room,
                    invite_by: Optional[User] = None) -> None:
        self.accounts[client.user_id].add_room(room, invite_by)


    def on_rename_room(self, client: MatrixClient, room: Room) -> None:
        self.accounts[client.user_id].rooms[room.room_id].update_ui()


    def on_left_room(self, client: MatrixClient, room_id: str) -> None:
        self.accounts[client.user_id].del_room(room_id)


    def really_clear_selection(self) -> None:
        self.clearSelection()
        self.setCurrentItem(None)


    # pylint: disable=invalid-name
    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Escape:
            self.really_clear_selection()


    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)

        if not self.itemAt(event.pos()):
            self.really_clear_selection()


    def sizeHint(self) -> QSize:
        cols = sum([self.columnWidth(c) for c in range(self.columnCount())])
        return QSize(max(cols, min(self.window.width() // 3, 360)), -1)


class BlankRow(QTreeWidgetItem):
    pass


class AccountRow(QTreeWidgetItem):
    def __init__(self, parent: UserTree, client: MatrixClient) -> None:
        super().__init__(parent)
        self.user_tree: UserTree           = parent
        self.client:    MatrixClient       = client
        self.rooms:     Dict[str, RoomRow] = {}

        self.auto_expanded_once: bool = False
        self.update_ui()


    def update_ui(self) -> None:
        self.setText(0, USER_DISPLAY_NAMES.get(self.client))
        self.setToolTip(0, self.client.user_id)


    def get_context_menu_actions(self) -> List[QAction]:
        return [actions.DelAccount(self.user_tree, self.client)]


    def add_room(self, room: Room, invite_by: Optional[User] = None) -> None:
        if room.room_id in self.rooms:
            print(f"WARN Duplicate: {room}")
            return

        self.rooms[room.room_id] = RoomRow(self, room, invite_by)
        self.sortChildren(0, Qt.AscendingOrder)

        if not self.auto_expanded_once:
            self.setExpanded(True)  # TODO: unless user collapsed manually
            self.auto_expanded_once = True


    def del_room(self, room_id: str) -> None:
        if room_id in self.rooms:
            self.removeChild(self.rooms[room_id])
            del self.rooms[room_id]


class RoomRow(QTreeWidgetItem):
    def __init__(self,
                 parent:    AccountRow,
                 room:      Room,
                 invite_by: Optional[User] = None) -> None:
        super().__init__(parent)
        self.account_row: AccountRow     = parent
        self.room:        Room           = room
        self.invite_by:   Optional[User] = invite_by

        self.setTextAlignment(1, Qt.AlignRight)  # msg unread/invite indicator
        self.update_ui()


    def update_ui(self) -> None:
        texts    = [ROOM_DISPLAY_NAMES.get(self.room), ""]
        tooltips = self.room.aliases + [self.room.room_id]

        if self.invite_by:
            texts[1] = "?"
            tooltips.insert(
                0, f"Pending invitation from {self.invite_by.user_id}"
            )

        for col, txt in enumerate(texts):
            self.setText(col, txt)

        tooltips = "\n".join(tooltips)
        for col in range(self.columnCount()):
            self.setToolTip(col, tooltips)


    def on_activation(self) -> None:
        client = self.account_row.client

        if self.invite_by:
            dialog = AcceptRoomInvite(
                client.user_id, self.text(0), self.invite_by.user_id
            )
            dialog.exec()
            clicked = dialog.clickedButton()

            if clicked is dialog.yes:
                self.accept_invite()
            elif clicked is dialog.no:
                self.decline_invite()
            else:
                return

        self.account_row.user_tree.window.go_to_chat_dock(client, self.room)


    def get_context_menu_actions(self) -> List[QAction]:
        tree = self.account_row.user_tree
        return [actions.LeaveRoom(tree, self.room, self.leave)]


    def ensure_is_invited(self) -> None:
        if not self.invite_by:
            raise RuntimeError(f"No invitation for {self.room.room_id}.")


    def accept_invite(self) -> None:
        self.ensure_is_invited()
        self.account_row.client.join_room(self.room.room_id)
        self.invite_by = None
        self.update_ui()


    def decline_invite(self) -> None:
        self.ensure_is_invited()
        self.leave()


    def leave(self) -> None:
        try:
            self.room.leave()
        except KeyError:  # matrix_client bug
            pass
        self.account_row.del_room(self.room.room_id)
