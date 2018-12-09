# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import webbrowser
from typing import Callable, Optional, Sequence

from matrix_client.room import Room
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QWidget

from . import __about__, dialogs, get_icon, menu

KEYS_BOUND = {}


# General functions

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
                 parent:           QWidget,
                 text:             str,
                 tooltip:          str = "",
                 icon:             str = "",
                 shortcut:         str = "",
                 multiselect_text: str = "") -> None:
        super().__init__(parent)
        self.parent           = parent
        self.multiselect_text = multiselect_text
        self.setText(text)

        tooltip = "\n".join((tooltip, shortcut)).strip()
        if tooltip:
            self.setToolTip(tooltip)

        self.icon_str = icon
        if icon:
            self.setIcon(get_icon(icon))

        self.shortcut_str = shortcut
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


class MultiselectAction(Action):
    def __init__(self, actions: Sequence[Action]) -> None:
        super().__init__(
            parent   = actions[0].parent,
            text     = actions[0].multiselect_text,
            tooltip  = actions[0].toolTip(),
            icon     = actions[0].icon_str,
            shortcut = actions[0].shortcut_str
        )
        self.actions = actions

    def on_trigger(self, checked: bool) -> None:
        for act in self.actions:
            act.on_trigger(checked)

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
        self.setMenu(menu.Menu(parent, actions))


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

class LeaveRoom(Action):
    def __init__(self,
                 parent:     QWidget,
                 room:       Room,
                 leave_func: Optional[Callable[[], None]]= None
                ) -> None:
        super().__init__(
            parent           = parent,
            text             = "&Leave room",
            tooltip          = "Leave and remove this room from the list",
            icon             = "leave.png",
            multiselect_text = "&Leave selected rooms",
        )
        self.room       = room
        self.leave_func = leave_func

    def on_trigger(self, _) -> None:
        if callable(self.leave_func):
            self.leave_func()
        else:
            self.room.leave()

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
        self.setMenu(menu.Menu(parent, actions))

class StatusAction(Action):
    def __init__(self, parent, text = None, shortcut = None) -> None:
        name = type(self).__name__
        super().__init__(
            parent   = parent,
            text     = text or f"&{name}",
            tooltip  = f"Change status for all accounts to {name.lower()}",
            icon     = f"status_{name.lower()}.png",
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
            icon     = "account_add.png",
            shortcut = "Ctrl+Shift+A",
        )
        actions = [a(parent) for a in (Login, Register)]
        self.setMenu(menu.Menu(parent, actions))

class DelAccount(Action):
    def __init__(self, parent: QWidget, user_id: str) -> None:
        super().__init__(
            parent   = parent,
            icon     = "account_del.png",
            text     = "Remove &account",
            tooltip  = ("Remove this account from Harmony\n"
                        "The account will still exist on the server and can "
                        "be added again later"),
            multiselect_text = "&Remove selected accounts",
        )
        self.user_id = user_id

    def on_trigger(self, _) -> None:
        self.parent.window.accounts.remove(self.user_id)

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
