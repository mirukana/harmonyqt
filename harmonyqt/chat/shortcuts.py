# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Any, Callable, Dict, Generator, List

from PyQt5.QtWidgets import QShortcut

from . import Chat
from .. import app

SHORTCUTS: Dict[Callable[[Chat], Any], List[str]] = {
    # Alt+direction simple scroll
    lambda c: c.messages.scroller.go_left():  ["A-h", "A-Left"],
    lambda c: c.messages.scroller.go_down():  ["A-j", "A-Down"],
    lambda c: c.messages.scroller.go_up():    ["A-k", "A-Up"],
    lambda c: c.messages.scroller.go_right(): ["A-l", "A-Right"],

    # Ctrl+Alt+direction page scroll
    lambda c: c.messages.scroller.go_page_left():  ["C-A-h", "C-A-Left"],
    lambda c: c.messages.scroller.go_page_down():  ["C-A-j", "C-A-Down"],
    lambda c: c.messages.scroller.go_page_up():    ["C-A-k", "C-A-Up"],
    lambda c: c.messages.scroller.go_page_right(): ["C-A-l", "C-A-Right"],

    # Ctrl+Alt+Shift+direction begin/end scroll
    lambda c: c.messages.scroller.go_min_left():  ["C-A-S-h", "C-A-S-Left"],
    lambda c: c.messages.scroller.go_bottom():    ["C-A-S-j", "C-A-S-Down"],
    lambda c: c.messages.scroller.go_top():       ["C-A-S-k", "C-A-S-Up"],
    lambda c: c.messages.scroller.go_max_right(): ["C-A-S-l", "C-A-S-Right"],
}


def execute_if_focused(chat: Chat, func: Callable[[Chat], Any]) -> None:
    focused = app().focused_chat_dock
    if focused is not None and focused.chat is chat:
        func(chat)


def get_shortcuts(chat: Chat) -> Generator[None, None, QShortcut]:
    for func, binds in SHORTCUTS.items():
        for bind in binds:
            bind = bind.replace("C-", "Ctrl+")\
                       .replace("A-", "Alt+")\
                       .replace("S-", "Shift+")

            qs = QShortcut(bind, chat)
            qs.activated.connect(lambda c=chat, f=func: f(c))
            qs.activatedAmbiguously.connect(
                lambda c=chat, f=func: execute_if_focused(c, f)
            )
            yield qs
