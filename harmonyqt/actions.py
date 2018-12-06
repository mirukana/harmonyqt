# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import webbrowser
from typing import List

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMenu, QWidget

from . import __about__, dialogs, get_icon

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
            self.setIcon(get_icon(icon))

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
            icon     = "new_chat.png",
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
            icon     = "direct_chat.png",
            shortcut = "Ctrl+Shift+D",
        )

    def on_trigger(self, _) -> None:
        dialogs.DirectChat(self.parent.window()).open_modeless()

class CreateRoom(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Create room",
            tooltip  = "Create a new chat room",
            icon     = "create_room.png",
            shortcut = "Ctrl+Shift+C",
        )

    def on_trigger(self, _) -> None:
        dialogs.CreateRoom(self.parent.window()).open_modeless()

class JoinRoom(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Join room",
            tooltip  = "Join an existing chat room",
            icon     = "join_room.png",
            shortcut = "Ctrl+Shift+J",
        )


# Status

class SetStatus(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Status",
            tooltip  = "Change status for all accounts",
            icon     = "status_set.png",
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
            icon     = "status_{name.lower()}.png",
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
            tooltip  = "Add a new account to Harmony",
            icon     = "add_account.png",
            shortcut = "Ctrl+Shift+A",
        )
        actions = [a(parent) for a in (Login, Register)]
        self.setMenu(Menu(parent, actions))

class Login(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Login",
            tooltip  = "Login to an existing Matrix account",
            icon     = "login.png",
            shortcut = "Ctrl+Shift+L",
        )

    def on_trigger(self, _) -> None:
        dialogs.Login(self.parent.window()).open_modeless()


class Register(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Register",
            tooltip  = "Register a new Matrix account",
            icon     = "register.png",
            shortcut = "Ctrl+Shift+R",
        )


    def on_trigger(self, _) -> None:
        webbrowser.open_new_tab("https://riot.im/app")


# Interface

class ToggleTitleBars(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Toggle title bars",
            tooltip  = "Toggle showing dock title bars\n" \
                       "In hidden mode, hold Alt to temporarily show them",
            icon     = "ui_view.png",
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
            icon     = "preferences.png",
            shortcut = "Ctrl+Shift+P",
        )
