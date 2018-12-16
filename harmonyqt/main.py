# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Dict, List, Optional, Tuple

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QApplication, QDesktopWidget, QMainWindow, QTabWidget, QWidget
)

from . import (
    __about__, accounts, app, chat, events, homepage, messages, theming,
    toolbar, usertree
)
from .dock import Dock


class App(QApplication):
    def __init__(self, argv: Optional[List[str]] = None) -> None:
        super().__init__(argv or [])
        # if not self.styleSheet:  # user can load one with --stylesheet
            # self.
            # pass

        self.focused_chat_dock: Optional[chat.ChatDock] = None
        self.focusChanged.connect(self.on_focus_change)


    def on_focus_change(self, _: QWidget, new: QWidget) -> None:
        while not isinstance(new, chat.ChatDock):
            if new is None:
                return
            new = new.parent()

        self.focused_chat_dock = new


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.title_bars_shown       = False
        self.alt_title_bars_toggled = False


    def construct(self) -> None:
        # pylint: disable=attribute-defined-outside-init
        # Can't define all that __init__ instead.
        # The UI elements need _MAIN_WINDOW to be set, see run() in __init__.

        # Setup appearance:

        self.setWindowTitle("Harmony")
        screen = QDesktopWidget().screenGeometry()
        self.resize(min(screen.width(), 800), min(screen.height(), 600))

        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        self.theme = theming.Theme("glass")
        self.icons = theming.Icons("flat_white")
        self.setStyleSheet(self.theme.style("interface"))


        # Setup main classes and event listeners:

        self.accounts = accounts.AccountManager()
        self.events   = events.EventManager()
        self.messages = messages.MessageProcessor()

        self.events.signal.left_room.connect(self.remove_chat_dock)
        self.events.signal.room_rename.connect(self.update_chat_dock_name)
        # Triggered by room renames that happen when account changes
        # self.events.signal.account_change.connect(self.update_chat_dock_name)


        # Setup docks:

        self.setDockNestingEnabled(True)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)
        # self.setTabShape(QTabWidget.Triangular)

        self.tree_dock = Dock("Accounts", self)
        self.tree_dock.setWidget(usertree.UserTree())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        self.home_dock = Dock("Home", self)
        self.home_dock.setWidget(homepage.HomePage())
        self.addDockWidget(Qt.RightDockWidgetArea, self.home_dock)

        # {(user_id, room_id): dock}
        self.chat_docks: Dict[Tuple[str, str], chat.ChatDock] = {}

        self.actions_dock = Dock("Actions", self)
        self.actions_dock.setWidget(toolbar.ActionsBar())
        self.addDockWidget(
            Qt.LeftDockWidgetArea, self.actions_dock, Qt.Vertical
        )


        # Run:

        self.show()

        try:
            self.accounts.login_using_config()
        except FileNotFoundError:
            pass


    def show_dock_title_bars(self, show: Optional[bool] = None) -> None:
        if show is None:
            show = not self.title_bars_shown

        docks = (self.tree_dock, self.actions_dock, self.home_dock,
                 *self.chat_docks.values())

        for dock in docks:
            dock.show_title_bar(show)

        self.title_bars_shown = show


    def go_to_chat_dock(self, user_id: str, room_id: str,
                        force_new_tab: bool = False) -> None:
        dock = self.chat_docks.get((user_id, room_id))
        if dock:
            print("focus")
            dock.focus()
            return

        def new_tabbed_dock() -> chat.ChatDock:
            dock = chat.ChatDock(user_id, room_id, self, self.title_bars_shown)
            self.tabifyDockWidget(self.home_dock, dock)
            return dock

        if force_new_tab:
            print("force")
            dock = new_tabbed_dock()
        else:
            dock = app().focused_chat_dock or self.home_dock
            print(dock)

            if isinstance(dock, chat.ChatDock):
                print("isinst")
                self.chat_docks.pop((dock.user_id, dock.room_id), None)
                dock.change_room(user_id, room_id)
            else:
                print("notinst")
                self.home_dock.hide()
                dock = new_tabbed_dock()

        self.chat_docks[(user_id, room_id)] = dock
        dock.focus()
        print(dock, "\n")


    def remove_chat_dock(self, user_id: str, room_id: str) -> None:
        dock = self.chat_docks.get((user_id, room_id))
        if dock:
            dock.hide()
            del self.chat_docks[(user_id, room_id)]


    def update_chat_dock_name(self, user_id: str, room_id: str) -> None:
        dock = self.chat_docks.get((user_id, room_id))
        if dock:
            dock.update_title()


    # pylint: disable=invalid-name
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.title_bars_shown and not self.alt_title_bars_toggled and \
           event.key() == Qt.Key_Alt:
            self.show_dock_title_bars(True)
            self.alt_title_bars_toggled = True


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if self.alt_title_bars_toggled and event.key() == Qt.Key_Alt:
            self.show_dock_title_bars(False)
            self.alt_title_bars_toggled = False
