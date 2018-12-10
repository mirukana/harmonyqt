# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import webbrowser
from multiprocessing.pool import ThreadPool
from typing import Callable, Optional, Sequence

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QWidget

from . import __about__, dialogs, get_icon, main_window, menu

ImmediateFunc = Optional[Callable[[], None]]

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
                 parent:              QWidget,
                 text:                str,
                 tooltip:             str           = "",
                 icon:                str           = "",
                 shortcut:            str           = "",
                 multiselect_text:    str           = "",
                 multiselect_tooltip: str           = "",
                 immediate_func:      ImmediateFunc = None,
                 thread_triggers:     bool          = False) -> None:
        super().__init__(parent)
        self.parent              = parent
        self.multiselect_text    = multiselect_text
        self.multiselect_tooltip = multiselect_tooltip
        self.immediate_func      = immediate_func
        self.thread_triggers     = thread_triggers
        self._pool               = ThreadPool(8)

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

        self.triggered.connect(self._on_trig)

    def _on_trig(self, checked: bool) -> None:
        if self.immediate_func:
            self.immediate_func()

        if self.thread_triggers:
            self._pool.apply_async(self.on_trigger, (checked,))
        else:
            self.on_trigger(checked)

    def on_trigger(self, checked: bool) -> None:
        pass


class MultiselectAction(Action):
    def __init__(self, actions: Sequence[Action]) -> None:
        super().__init__(
            parent          = actions[0].parent,
            text            = actions[0].multiselect_text,
            tooltip         = actions[0].multiselect_tooltip,
            icon            = actions[0].icon_str,
            shortcut        = actions[0].shortcut_str,
            thread_triggers = actions[0].thread_triggers,
        )
        self.actions         = actions
        self._pool           = ThreadPool(8)
        self.immediate_funcs = [a.immediate_func for a in actions
                                if a.immediate_func]

    def _on_trig(self, checked: bool) -> None:
        for func in self.immediate_funcs:
            func()
        self.on_trigger(checked)

    def on_trigger(self, checked: bool) -> None:
        if self.thread_triggers:
            self._pool.map_async(lambda a: a.on_trigger(checked), self.actions)
        else:
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
        dialogs.CreateRoom().open_modeless()

class JoinRoom(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Join room",
            tooltip  = "Join an existing chat room",
            icon     = "join_room.png",
            shortcut = "Ctrl+Shift+J",
        )

class InviteToRoom(Action):
    def __init__(self, parent: QWidget, room: Room, as_user: str = "") -> None:
        tooltip = "Invite a user to join selected room"
        super().__init__(
            parent              = parent,
            text                = "&Invite to room",
            icon                = "invite.png",
            tooltip             = tooltip,
            multiselect_text    = "&Invite to selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms")
        )
        self.room    = room
        self.as_user = as_user

    def on_trigger(self, _) -> None:
        dialogs.InviteToRoom(self.room, self.as_user).open_modeless()

class LeaveRoom(Action):
    def __init__(self, parent: QWidget, room: Room,
                 immediate_func: ImmediateFunc = None) -> None:
        tooltip = "Leave and remove selected room from the list"
        super().__init__(
            parent              = parent,
            text                = "&Leave room",
            icon                = "leave.png",
            tooltip             = tooltip,
            multiselect_text    = "&Leave selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
            thread_triggers     = True,
        )
        self.room = room

    def on_trigger(self, _) -> None:
        try:
            self.room.leave()
        except KeyError:  # matrix_client bug
            pass

class AcceptInvite(Action):
    def __init__(self, parent: QWidget, room: Room,
                 immediate_func: ImmediateFunc = None) -> None:
        tooltip = "Accept invitation and join selected room"
        super().__init__(
            parent              = parent,
            text                = "&Accept invitation",
            icon                = "accept_small.png",
            tooltip             = tooltip,
            multiselect_text    = "&Accept invitations for selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
            thread_triggers     = True,
        )
        self.room = room

    def on_trigger(self, _) -> None:
        try:
            self.room.client.join_room(self.room.room_id)
        except MatrixRequestError as err:
            data = json.loads(err.content)
            if data["errcode"] == "M_UNKNOWN":
                print("Room gone, error box not implemented")

class DeclineInvite(Action):
    def __init__(self, parent: QWidget, room: Room,
                 immediate_func: ImmediateFunc = None) -> None:
        tooltip = "Decline invitation for selected room"
        super().__init__(
            parent              = parent,
            text                = "&Decline invitation",
            icon                = "cancel_small.png",
            tooltip             = tooltip,
            multiselect_text    = "&Decline invitations for selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
            thread_triggers     = True,
        )
        self.room           = room
        self._leave         = LeaveRoom(parent, room, immediate_func)
        self.on_trigger     = self._leave.on_trigger


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
            thread_triggers = True,
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
        tooltip  = "Remove selected account from Harmony\n" \
                   "The account will still exist on the server and can " \
                   "be added again later"
        super().__init__(
            parent              = parent,
            icon                = "account_del.png",
            text                = "Remove &account",
            tooltip             = tooltip,
            multiselect_text    = "&Remove selected accounts",
            multiselect_tooltip = tooltip.replace("account", "accounts")
        )
        self.user_id = user_id

    def on_trigger(self, _) -> None:
        main_window().accounts.remove(self.user_id)

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
        dialogs.Login().open_modeless()


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
        main_window().show_dock_title_bars()


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
