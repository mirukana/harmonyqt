# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMessageBox


class AcceptRoomInvite(QMessageBox):
    def __init__(self, user_id: str, room_name: str, inviter_id: str) -> None:
        super().__init__()
        from .. import STYLESHEET
        self.setStyleSheet(STYLESHEET)
        self.setWindowTitle("Harmony - Accept room invitation")

        self.setText(f"<b>{user_id}</b> has been invited to join the "
                     f"room <b>{room_name}</b> by <b>{inviter_id}</b>.")

        self.yes    = self.addButton("Accept",  QMessageBox.YesRole)
        self.no     = self.addButton("Decline", QMessageBox.NoRole)
        self.cancel = self.addButton("Cancel",  QMessageBox.RejectRole)

        self.setDefaultButton(self.yes)
        self.setIcon(QMessageBox.Question)
