# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import webbrowser
from typing import Callable, Dict, Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QWidget

from matrix_client.errors import MatrixRequestError
from matrix_client.room import Room

from . import __about__, dialogs, main_window, menu

ImmediateFunc = Optional[Callable[[], None]]

KEYS_BOUND: Dict[str, str] = {}


class KeysAlreadyBoundError(Exception):
    def __init__(self, key: str, action: str, bound_to: str) -> None:
        super().__init__(f"Can't set {key!r} for action {action!r}, "
                         f"already bound to {bound_to!r}.")
        self.key      = key
        self.action   = action
        self.bound_to = bound_to


# General functions

def safe_bind(action: QAction, key: str) -> str:
    name = type(action).__name__

    if key in KEYS_BOUND and KEYS_BOUND[key] != name:
        raise KeysAlreadyBoundError(key, name, KEYS_BOUND[key])

    KEYS_BOUND[key] = name
    return key


# Base classes

class Action(QAction):
    def __init__(self,
                 parent:              QWidget,
                 text:                str           = "",
                 tooltip:             str           = "",
                 icon:                str           = "",
                 shortcut:            str           = "",
                 multiselect_text:    str           = "",
                 multiselect_tooltip: str           = "",
                 immediate_func:      ImmediateFunc = None) -> None:
        super().__init__(parent)
        self.parent              = parent
        self.text                = text
        self.tooltip             = "\n".join((tooltip, shortcut)).strip()
        self.icon_str            = icon
        self.shortcut_str        = shortcut
        self.multiselect_text    = multiselect_text
        self.multiselect_tooltip = multiselect_tooltip
        self.immediate_func      = immediate_func

        self.setText(self.text)

        if self.tooltip:
            self.setToolTip(tooltip)

        if icon:
            self.setIcon(main_window().icons.icon(icon))

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

        self.on_trigger(checked)

    def on_trigger(self, checked: bool) -> None:
        pass


class MultiselectAction(Action):
    def __init__(self, actions: Sequence[Action]) -> None:
        super().__init__(
            parent   = actions[0].parent,
            text     = actions[0].multiselect_text,
            tooltip  = actions[0].multiselect_tooltip or actions[0].tooltip,
            icon     = actions[0].icon_str,
            shortcut = actions[0].shortcut_str,
        )
        self.actions         = actions
        self.immediate_funcs = [a.immediate_func for a in actions
                                if a.immediate_func]

    def _on_trig(self, checked: bool) -> None:
        for func in self.immediate_funcs:
            func()
        self.on_trigger(checked)

    def on_trigger(self, checked: bool) -> None:
        for act in self.actions:
            act.on_trigger(checked)

# Rooms

class NewChat(Action):
    def __init__(self, parent: QWidget, for_user_id: str = "") -> None:
        super().__init__(
            parent  = parent,
            text    = "&New chat",
            tooltip = "Create/join a chat room",
            icon    = "new_chat",
        )
        acts = [a(parent, for_user_id)
                for a in (DirectChat, CreateRoom, JoinRoom)]
        self.setMenu(menu.Menu(parent, acts))


class DirectChat(Action):
    def __init__(self, parent: QWidget, for_user_id: str = "") -> None:
        super().__init__(
            parent   = parent,
            text     = "&Direct chat",
            tooltip  = "Start a direct chat with another user",
            icon     = "direct_chat",
            shortcut = "Ctrl+Shift+D" if not for_user_id else "",
        )
        self.for_user_id = for_user_id
        self.setDisabled(True)

class CreateRoom(Action):
    def __init__(self, parent: QWidget, for_user_id: str = "") -> None:
        super().__init__(
            parent   = parent,
            text     = "&Create room",
            tooltip  = "Create a new chat room",
            icon     = "create_room",
            shortcut = "Ctrl+Shift+C" if not for_user_id else "",
        )
        self.for_user_id = for_user_id

    def on_trigger(self, checked: bool) -> None:
        dialogs.CreateRoom(self.for_user_id).open_modeless()

class JoinRoom(Action):
    def __init__(self, parent: QWidget, for_user_id: str = "") -> None:
        super().__init__(
            parent   = parent,
            text     = "&Join room",
            tooltip  = "Join an existing chat room",
            icon     = "join_room",
            shortcut = "Ctrl+Shift+J" if not for_user_id else "",
        )
        self.for_user_id = for_user_id
        self.setDisabled(True)

class InviteToRoom(Action):
    def __init__(self, parent: QWidget, room: Room, as_user: str = "") -> None:
        tooltip = "Invite a user to join selected room"
        super().__init__(
            parent              = parent,
            text                = "&Invite to room",
            icon                = "invite",
            tooltip             = tooltip,
            multiselect_text    = "&Invite to selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms")
        )
        self.room    = room
        self.as_user = as_user

    def on_trigger(self, checked: bool) -> None:
        dialogs.InviteToRoom(self.room, self.as_user).open_modeless()

class LeaveRoom(Action):
    def __init__(self, parent: QWidget, room: Room,
                 immediate_func: ImmediateFunc = None) -> None:
        tooltip = "Leave and remove selected room from the list"
        super().__init__(
            parent              = parent,
            text                = "&Leave room",
            icon                = "leave",
            tooltip             = tooltip,
            multiselect_text    = "&Leave selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
        )
        self.room = room

    def on_trigger(self, checked: bool) -> None:
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
            icon                = "accept_small",
            tooltip             = tooltip,
            multiselect_text    = "&Accept invitations for selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
        )
        self.room = room

    def on_trigger(self, checked: bool) -> None:
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
            icon                = "cancel_small",
            tooltip             = tooltip,
            multiselect_text    = "&Decline invitations for selected rooms",
            multiselect_tooltip = tooltip.replace("room", "rooms"),
            immediate_func      = immediate_func,
        )
        self.room           = room
        self._leave         = LeaveRoom(parent, room, immediate_func)

    def on_trigger(self, checked: bool) -> None:
        self._leave.on_trigger(checked)


# Status

class SetStatus(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Status",
            tooltip  = "Change status for all accounts",
            icon     = "status_set_tmp_disabled",
        )
        acts = [a(parent) for a in (Online, Away, Invisible, Offline)]
        self.setMenu(menu.Menu(parent, acts))
        self.setDisabled(True)

class StatusAction(Action):
    def __init__(self, parent, text = None, shortcut = None) -> None:
        name = type(self).__name__
        super().__init__(
            parent   = parent,
            text     = text or f"&{name}",
            tooltip  = f"Change status for all accounts to {name.lower()}",
            icon     = f"status_{name.lower()}",
            shortcut = shortcut or f"Ctrl+Alt+{name[0].upper()}",
        )
        self.setDisabled(True)

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
            icon     = "account_add",
        )
        acts = [a(parent) for a in (Login, Register)]
        self.setMenu(menu.Menu(parent, acts))

class DelAccount(Action):
    def __init__(self, parent: QWidget, user_id: str) -> None:
        tooltip  = "Remove selected account from Harmony\n" \
                   "The account will still exist on the server and can " \
                   "be added again later"
        super().__init__(
            parent              = parent,
            icon                = "account_del",
            text                = "Remove &account",
            tooltip             = tooltip,
            multiselect_text    = "&Remove selected accounts",
            multiselect_tooltip = tooltip.replace("account", "accounts")
        )
        self.user_id = user_id

    def on_trigger(self, checked: bool) -> None:
        main_window().accounts.remove(self.user_id)

class Login(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Login",
            tooltip  = "Login to an existing Matrix account",
            icon     = "login",
            shortcut = "Ctrl+Shift+L",
        )

    def on_trigger(self, checked: bool) -> None:
        dialogs.Login().open_modeless()


class Register(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Register",
            tooltip  = "Register a new Matrix account",
            icon     = "register",
            shortcut = "Ctrl+Shift+R",
        )


    def on_trigger(self, checked: bool) -> None:
        webbrowser.open_new_tab("https://riot.im/app")


# Interface

class ToggleTitleBars(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Toggle title bars",
            tooltip  = "Toggle showing dock title bars",
            icon     = "ui_view",
            shortcut = "Ctrl+Shift+T",
        )

    def on_trigger(self, checked: bool) -> None:
        main_window().show_dock_title_bars()


# Settings

class Preferences(Action):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            parent   = parent,
            text     = "&Preferences",
            tooltip  = "Change preferences",
            icon     = "preferences_tmp_disabled",
            shortcut = "Ctrl+Shift+P",
        )
        self.setDisabled(True)
