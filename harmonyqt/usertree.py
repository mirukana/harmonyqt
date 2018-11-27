# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

# pylint: disable=no-name-in-module
# from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem

from . import __about__, accounts


class UserTree(QTreeWidget):
    def __init__(self,
                 accs:   accounts.LoggedAccountsType,
                 window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window

        self.setColumnCount(1)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setAutoExpandDelay(500)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)  # double click = open page
        # self.setIndentation(0)

        self.itemActivated.connect(self.on_row_click)

        self.accounts = accs
        self.build_rows()
        # self.setSortingEnabled(True)
        self.expandToDepth(0)


    def build_rows(self) -> None:
        for i_acc, (user_id, account) in enumerate(self.accounts.items()):
            if i_acc > 0:
                QTreeWidgetItem(self)

            account_row      = QTreeWidgetItem(self)
            account_row.user = account.user
            display_name     = account.user.get_display_name()
            account_row.setText(0, f"• {display_name}")
            account_row.setToolTip(0, user_id)

            for room_id, room in account.client.rooms.items():
                room_row      = QTreeWidgetItem(account_row)
                room_row.room = room
                room_row.setText(0, room.display_name)
                room_row.setToolTip(0, "\n".join(room.aliases + [room_id]))

                for member in room.get_joined_members():
                    member_row        = QTreeWidgetItem(room_row)
                    member_row.member = member
                    member_row.setText(0, f"• {member.get_display_name()}")
                    member_row.setToolTip(0, member.user_id)


    def on_row_click(self, row: QTreeWidgetItem, _: int) -> None:
        if hasattr(row, "room"):
            self.window.go_to_chat_dock(row.room, row.parent().user)
