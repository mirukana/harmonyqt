# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from PyQt5.QtWidgets import QMessageBox, QWidget

from .. import actions, main_window


class AcceptRoomInvite(QMessageBox):
    def __init__(self, parent: QWidget, room, room_name: str, inviter_id: str
                ) -> None:
        super().__init__(parent)
        self.setStyleSheet(main_window().theme.style("interface"))
        self.setWindowOpacity(0.9)
        self.setWindowTitle("Harmony - Accept room invitation")

        user_id = room.client.user_id
        self.setText(f"<b>{user_id}</b> has been invited to join the "
                     f"room <b>{room_name}</b> by <b>{inviter_id}</b>.")

        self.yes    = self.addButton("Accept",  QMessageBox.YesRole)
        self.no     = self.addButton("Decline", QMessageBox.NoRole)
        self.cancel = self.addButton("Cancel",  QMessageBox.RejectRole)

        self.yes.clicked.connect(actions.AcceptInvite(self, room).on_trigger)
        self.no.clicked.connect(actions.DeclineInvite(self, room).on_trigger)

        self.setDefaultButton(self.yes)
        self.setIcon(QMessageBox.Question)
