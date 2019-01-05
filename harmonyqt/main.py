# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QDesktopWidget, QMainWindow, QTabWidget, QWidget
)

from . import (
    __about__, accounts, app, event_logger, events, homepage, shortcuts,
    theming, toolbar, usertree
)
from .chat import ChatDock
from .dock import Dock


class App(QApplication):
    def __init__(self, argv: Optional[List[str]] = None) -> None:
        super().__init__(argv or [])
        # if not self.styleSheet:  # user can load one with --stylesheet
            # self.
            # pass

        self.focused_chat_dock: Optional[ChatDock] = None
        self.focusChanged.connect(self.on_focus_change)


    def on_focus_change(self, _: QWidget, new: QWidget) -> None:
        while not isinstance(new, ChatDock):
            if new is None:
                return
            new = new.parent()

        self.focused_chat_dock = new


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.title_bars_shown = False


    def construct(self) -> None:
        # pylint: disable=attribute-defined-outside-init
        # Can't define all that __init__ instead.
        # The UI elements need _MAIN_WINDOW to be set, see run() in __init__.

        # Setup appearance:

        self.setWindowTitle("Harmony")
        screen = QDesktopWidget().screenGeometry()
        self.resize(min(screen.width(), 1152), min(screen.height(), 768))

        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        self.theme = theming.Theme("glass")
        self.icons = theming.Icons("flat_white")
        self.setStyleSheet(self.theme.style("interface"))


        # Setup main classes and event listeners:

        self.event_logger = event_logger.EventLogger()
        self.accounts     = accounts.AccountManager()
        self.events       = events.EventManager()

        self.event_logger.start()

        self.events.signals.left_room.connect(self.remove_chat_dock)
        self.events.signals.room_rename.connect(self.update_chat_dock_name)
        # Triggered by room renames that happen when account changes
        # self.events.signal.account_change.connect(self.update_chat_dock_name)


        # Setup main UI parts:

        self.setDockNestingEnabled(True)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)

        self.tree_dock = Dock("Accounts / Rooms", self)
        self.tree_dock.setWidget(usertree.UserTree())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        self.actions_dock = Dock("Actions", self)
        self.actions_dock.setWidget(toolbar.ActionsBar())
        self.splitDockWidget(self.tree_dock, self.actions_dock, Qt.Vertical)

        self.home_dock = Dock("Home", self)
        self.home_dock.setWidget(homepage.HomePage())
        self.addDockWidget(Qt.RightDockWidgetArea, self.home_dock)

        # {(user_id, room_id): dock}
        self.visible_chat_docks: Dict[Tuple[str, str], ChatDock] = {}

        self.show_dock_title_bars(False)

        self.shortcuts = list(shortcuts.get_shortcuts())


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
                 *self.visible_chat_docks.values())

        for dock in docks:
            dock.show_title_bar(show)

        self.title_bars_shown = show


    def new_chat_dock(self,
                      user_id:            str,
                      room_id:            str,
                      previously_focused: ChatDock,
                      in_new:             str            = "",
                      split_orientation:  Qt.Orientation = Qt.Horizontal,
                     ) -> ChatDock:
        assert in_new in (None, "", "tab", "split")

        prev_is_in_tab = bool(self.tabifiedDockWidgets(previously_focused))
        dock = ChatDock(user_id, room_id, self)

        if not previously_focused.isVisible():
            self.addDockWidget(
                previously_focused.current_area or Qt.RightDockWidgetArea,
                dock,
                split_orientation
            )

        if in_new == "split" and prev_is_in_tab:
            area = None if previously_focused.isFloating() else \
                   previously_focused.current_area
            area = area or Qt.RightDockWidgetArea

            self.addDockWidget(area, dock, split_orientation)

        elif in_new == "split":
            self.splitDockWidget(previously_focused, dock, split_orientation)

        else:
            self.tabifyDockWidget(previously_focused, dock)

        return dock


    def go_to_chat_dock(self, user_id: str, room_id: str, in_new: str = "",
                        split_orientation: Qt.Orientation = Qt.Horizontal
                       ) -> None:

        dock = self.visible_chat_docks.get((user_id, room_id))
        if dock:
            dock.focus()
            return

        dock = app().focused_chat_dock
        if not dock or not dock.isVisible():
            dock = self.home_dock

        if in_new:
            dock = self.new_chat_dock(user_id, room_id, dock, in_new,
                                      split_orientation)
        elif isinstance(dock, ChatDock):
            dock.change_room(user_id, room_id)
        else:
            self.home_dock.hide()
            dock = self.new_chat_dock(user_id, room_id, dock, in_new,
                                      split_orientation)

        dock.focus()


    def remove_chat_dock(self, user_id: str, room_id: str) -> None:
        dock = self.visible_chat_docks.get((user_id, room_id))
        if dock:
            dock.hide()


    def update_chat_dock_name(self, user_id: str, room_id: str) -> None:
        dock = self.visible_chat_docks.get((user_id, room_id))
        if dock:
            dock.autoset_title()
