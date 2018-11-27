# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import sys
from pathlib import Path
from typing import List, Optional

from matrix_client.room import Room
from matrix_client.user import User
from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDockWidget, QMainWindow, QTabWidget

from . import __about__, accounts, chat, events, homepage, usertree

DEFAULT_STYLESHEET = resource_filename(__about__.__name__, "stylesheet.qss")


class HarmonyQt(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(__about__.__pkg_name__)
        self.resize(640, 480)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)
        self.setStyleSheet(Path(DEFAULT_STYLESHEET).read_text())

        self.setDockNestingEnabled(True)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)
        # self.setTabShape(QTabWidget.Triangular)

        self.accounts = accounts.login()
        self.events   = events.EventManager(self.accounts)

        self.tree_dock = QDockWidget("Accounts", self)
        self.tree_dock.setWidget(usertree.UserTree(self.accounts, self))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        self.home_dock = QDockWidget("Home", self)
        self.home_dock.setWidget(homepage.HomePage())
        self.home_dock.setFeatures(
            # Make it unclosable so we can always rely on it to append tabs
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.home_dock)

        self.chat_docks = []

        self.show()


    def go_to_chat_dock(self, room: Room, user: User) -> None:
        def go(dock: QDockWidget) -> None:
            dock.show()
            dock.raise_()
            dock.widget().sendbox.setFocus()

        for dock in self.chat_docks:
            if dock.widget().room == room and dock.widget().user == user:
                go(dock)
                return

        chat_ = chat.Chat(room=room, user=user, window=self)
        dock  = QDockWidget(f"{user.get_display_name()}: {room.display_name}",
                            self)
        dock.setWidget(chat_)
        self.tabifyDockWidget(self.home_dock, dock)
        go(dock)
        self.chat_docks.append(dock)


def run(argv: Optional[List[str]] = None) -> None:
    app = QApplication(argv or sys.argv)
    _   = HarmonyQt()

    # Make CTRL-C work
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec_())
