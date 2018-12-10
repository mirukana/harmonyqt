# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
from typing import Dict, List

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QHeaderView, QSizePolicy, QTreeWidget,
                             QTreeWidgetItem)

from . import main_window, __about__, actions
from .dialogs import AcceptRoomInvite
from .matrix import HMatrixClient
from .menu import Menu


class UserTree(QTreeWidget):
    def __init__(self) -> None:
        super().__init__()
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

        event_sig = main_window().events.signal
        event_sig.new_account.connect(self.add_account)
        event_sig.account_gone.connect(self.del_account)
        event_sig.new_room.connect(self.on_add_room)
        event_sig.new_invite.connect(self.on_add_room)
        event_sig.room_rename.connect(self.on_rename_room)
        event_sig.left_room.connect(self.on_left_room)
        event_sig.account_change.connect(self.on_account_change)


    def add_account(self, user_id: str) -> None:
        if user_id in self.accounts:
            return

        self.accounts[user_id] = AccountRow(self, user_id)

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


    def del_account(self, user_id: str) -> None:
        if user_id not in self.accounts:
            return

        to_del: AccountRow = self.accounts[user_id]
        root               = self.invisibleRootItem()

        for row in self.blank_rows:
            if root.indexOfChild(row) == root.indexOfChild(to_del) - 1:
                root.removeChild(row)

        root.removeChild(to_del)
        del self.accounts[user_id]

        first = root.child(0)
        if isinstance(first, BlankRow):
            root.removeChild(first)


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


    def on_add_room(self, user_id: str, room_id: str,
                    invite_by: str = "", display_name: str = "",
                    name:      str = "", alias:        str = "") -> None:
        self.accounts[user_id].add_room(room_id,
                                        invite_by, display_name, name, alias)


    def on_rename_room(self, user_id: str, room_id: str) -> None:
        rooms = self.accounts[user_id].rooms
        if room_id in rooms:
            rooms[room_id].update_ui()


    def on_left_room(self, user_id: str, room_id: str) -> None:
        self.accounts[user_id].del_room(room_id)


    def on_account_change(self, user_id: str, _: str,
                          new_display_name: str, new_avatar_url: str) -> None:
        self.accounts[user_id].update_ui(new_display_name, new_avatar_url)


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
        return QSize(max(cols, min(main_window().width() // 3, 360)), -1)


class BlankRow(QTreeWidgetItem):
    pass


class AccountRow(QTreeWidgetItem):
    def __init__(self, parent: UserTree, user_id: str) -> None:
        super().__init__(parent)
        self.user_tree: UserTree         = parent
        self.client:    HMatrixClient    = main_window().accounts[user_id]
        self.rooms:     Dict[str, RoomRow] = {}

        self.auto_expanded_once: bool = False
        self.update_ui()


    def update_ui(self, new_display_name: str = "", _: str = "") -> None:
        self.setText(0,
                     new_display_name or self.client.h_user.get_display_name())
        self.setToolTip(0, self.client.user_id)


    def get_context_menu_actions(self) -> List[QAction]:
        return [actions.DelAccount(self.user_tree, self.client.user_id)]


    def add_room(self, room_id: str,
                 invite_by: str = "", display_name: str = "",
                 name:      str = "", alias:        str = "") -> None:
        if room_id in self.rooms:
            self.rooms[room_id].update_ui()
            return

        self.rooms[room_id] = RoomRow(self, room_id,
                                      invite_by, display_name, name, alias)
        self.sortChildren(0, Qt.AscendingOrder)

        if not self.auto_expanded_once:
            self.setExpanded(True)  # TODO: unless user collapsed manually
            self.auto_expanded_once = True


    def del_room(self, room_id: str) -> None:
        if room_id in self.rooms:
            self.removeChild(self.rooms[room_id])
            del self.rooms[room_id]


class RoomRow(QTreeWidgetItem):
    def __init__(self, parent: AccountRow, room_id: str,
                 invite_by: str = "", display_name: str = "",
                 name:      str = "", alias:        str = "") -> None:
        super().__init__(parent)
        self.account_row: AccountRow = parent
        self.invite_by:   str        = invite_by

        if invite_by:
            self.room: Room           = Room(parent.client, room_id)
            self.room.name            = self.room.name            or name
            self.room.canonical_alias = self.room.canonical_alias or alias
        else:
            self.room: Room = parent.client.rooms[room_id]

        self.setTextAlignment(1, Qt.AlignRight)  # msg unread/invite indicator
        self.update_ui(display_name)


    def update_ui(self, invite_display_name: str = "") -> None:
        # The later crashes for rooms we're invited to but not joined
        dispname = invite_display_name or self.room.display_name

        texts    = [dispname, ""]
        tooltips = self.room.aliases + [self.room.room_id]

        if self.invite_by:
            texts[1] = "?"
            tooltips.insert(0, f"Pending invitation from {self.invite_by}")

        for col, txt in enumerate(texts):
            self.setText(col, txt)

        tooltips = "\n".join(tooltips)
        for col in range(self.columnCount()):
            self.setToolTip(col, tooltips)


    def on_activation(self) -> None:
        user_id = self.account_row.client.user_id

        if self.invite_by:
            dialog = AcceptRoomInvite(main_window(),
                                      user_id, self.text(0), self.invite_by)
            dialog.exec()
            clicked = dialog.clickedButton()

            if clicked is dialog.yes:
                self.accept_invite()
            elif clicked is dialog.no:
                self.decline_invite()
                return
            else:
                return

        main_window().go_to_chat_dock(user_id, self.room.room_id)


    def get_context_menu_actions(self) -> List[QAction]:
        tree    = self.account_row.user_tree
        user_id = self.account_row.client.user_id
        acts    = []

        if self.invite_by:
            acts += [
                actions.AcceptInvite(tree, self.room, self.on_invite_accept),
                actions.DeclineInvite(tree, self.room, self.on_leave)
            ]
        else:
            acts += [actions.InviteToRoom(tree, self.room, user_id),
                     actions.LeaveRoom(tree, self.room, self.on_leave)]
        return acts


    def on_invite_accept(self) -> None:
        self.invite_by = None
        self.update_ui()


    def on_leave(self) -> None:
        self.account_row.del_room(self.room.room_id)


    def ensure_is_invited(self) -> None:
        if not self.invite_by:
            raise RuntimeError(f"No invitation for {self.room.room_id}.")


    def accept_invite(self) -> None:
        self.ensure_is_invited()
        try:
            self.account_row.client.join_room(self.room.room_id)
        except MatrixRequestError as err:
            data = json.loads(err.content)
            if data["errcode"] == "M_UNKNOWN":
                print("Room gone, error box not implemented")

        self.invite_by = None
        self.update_ui()


    def decline_invite(self) -> None:
        self.ensure_is_invited()
        # self.leave()
