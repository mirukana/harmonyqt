# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import os
from typing import List

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QAction, QMenu, QWidget

from . import __about__

ICON_PACK = resource_filename(__about__.__name__, "icons/placeholder_white")

KEYS_BOUND = {}

def safe_bind(action: QAction, key: str) -> str:
    name = type(action).__name__

    if key in KEYS_BOUND:
        raise RuntimeError(f"Can't set {key!r} for action {name!r}, "
                           f"already bound to {KEYS_BOUND[key]!r}")

    KEYS_BOUND[key] = name
    return key


# Base classes

class Action(QAction):
    def __init__(self,
                 parent:   QWidget,
                 text:     str,
                 tooltip:  str = "",
                 icon:     str = "",
                 shortcut: str = "") -> None:
        super().__init__(parent)
        self.parent = parent
        self.setText(text)

        tooltip = "\n".join((tooltip, shortcut)).strip()
        if tooltip:
            self.setToolTip(tooltip)

        if icon:
            self.setIcon(QIcon(icon))

        if shortcut:
            self.setShortcutContext(Qt.ApplicationShortcut)
            self.setShortcut(QKeySequence(safe_bind(self, shortcut)))

            try:  # Qt >= 5.10
                self.setShortcutVisibleInContextMenu(True)
            except AttributeError:
                pass

        self.triggered.connect(self.on_trigger)


    def on_trigger(self, checked: bool) -> None:
        pass


class Menu(QMenu):
    def __init__(self, parent: QWidget, actions: List[QAction]) -> None:
        super().__init__(parent)
        self.setWindowOpacity(0.8)
        self.addActions(actions)
        self.setTearOffEnabled(True)
        self.setToolTipsVisible(True)


# Rooms

class NewChat(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&New chat",
            tooltip  = "Create/join a chat room",
            icon     = f"{ICON_PACK}{os.sep}new_chat.png",
            shortcut = "Ctrl+Shift+N",
        )
        actions = [a(parent) for a in (DirectChat, CreateRoom, JoinRoom)]
        self.setMenu(Menu(parent, actions))


class DirectChat(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Direct chat",
            tooltip  = "Start a direct chat with another user",
            icon     = f"{ICON_PACK}{os.sep}direct_chat.png",
            shortcut = "Ctrl+Shift+D",
        )

class CreateRoom(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "Create &room",
            tooltip  = "Create a new chat room",
            icon     = f"{ICON_PACK}{os.sep}create_room.png",
            shortcut = "Ctrl+Shift+R",
        )

class JoinRoom(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Join room",
            tooltip  = "Join an existing chat room",
            icon     = f"{ICON_PACK}{os.sep}join_room.png",
            shortcut = "Ctrl+Shift+J",
        )


# Status

class SetStatus(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Status",
            tooltip  = "Change status for all accounts",
            icon     = f"{ICON_PACK}{os.sep}status_set.png",
            shortcut = "Ctrl+Shift+S",
        )
        actions = [a(parent) for a in (Online, Away, Invisible, Offline)]
        self.setMenu(Menu(parent, actions))

class StatusAction(Action):
    def __init__(self, parent, text = None, shortcut = None) -> None:
        name = type(self).__name__
        super().__init__(
            parent   = parent,
            text     = text or f"&{name}",
            tooltip  = f"Change status for all accounts to {name.lower()}",
            icon     = f"{ICON_PACK}{os.sep}status_{name.lower()}.png",
            shortcut = shortcut or f"Ctrl+Alt+{name[0].upper()}",
        )

class Online(StatusAction):
    pass

class Away(StatusAction):
    pass

class Invisible(StatusAction):
    pass

class Offline(StatusAction):
    def __init__(self, parent):
        super().__init__(parent, text="O&ffline", shortcut="Ctrl+Alt+F")


# Accounts

class AddAccount(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "Add &account",
            tooltip  = "Login/register an account",
            icon     = f"{ICON_PACK}{os.sep}add_account.png",
            shortcut = "Ctrl+Shift+A",
        )


# Interface

class ToggleTitleBars(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Toggle title bars",
            tooltip  = "Toggle showing dock title bars\n" \
                       "In hidden mode, hold Alt to temporarily show them",
            icon     = f"{ICON_PACK}{os.sep}ui_view.png",
            shortcut = "Ctrl+Shift+T",
        )


    def on_trigger(self, _) -> None:
        self.parent.window().show_dock_title_bars()


# Settings

class Preferences(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Preferences",
            tooltip  = "Change preferences",
            icon     = f"{ICON_PACK}{os.sep}preferences.png",
            shortcut = "Ctrl+Shift+P",
        )
