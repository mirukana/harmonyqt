# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Any, Callable, Dict, Generator, List

from PyQt5.QtWidgets import QShortcut

from .display import MessageDisplay as MD
from .. import app

SHORTCUTS: Dict[Callable[[MD], Any], List[str]] = {
    # Alt+direction simple scroll
    lambda d: d.scroller.go_left():  ["A-h", "A-Left"],
    lambda d: d.scroller.go_down():  ["A-j", "A-Down"],
    lambda d: d.scroller.go_up():    ["A-k", "A-Up"],
    lambda d: d.scroller.go_right(): ["A-l", "A-Right"],

    # Ctrl+Alt+direction page scroll
    lambda d: d.scroller.go_page_left():  ["C-A-h", "C-A-Left"],
    lambda d: d.scroller.go_page_down():  ["C-A-j", "C-A-Down"],
    lambda d: d.scroller.go_page_up():    ["C-A-k", "C-A-Up"],
    lambda d: d.scroller.go_page_right(): ["C-A-l", "C-A-Right"],

    # Ctrl+Alt+Shift+direction begin/end scroll
    lambda d: d.scroller.go_min_left():  ["C-A-S-h", "C-A-S-Left"],
    lambda d: d.scroller.go_bottom():    ["C-A-S-j", "C-A-S-Down"],
    lambda d: d.scroller.go_top():       ["C-A-S-k", "C-A-S-Up"],
    lambda d: d.scroller.go_max_right(): ["C-A-S-l", "C-A-S-Right"],
}


def execute_if_focused(display: MD, func: Callable[[MD], Any]) -> None:
    focused = app().focused_chat_dock
    if focused is not None and focused.chat is display:
        func(display)


def get_shortcuts(display: MD) -> Generator[None, None, QShortcut]:
    for func, binds in SHORTCUTS.items():
        for bind in binds:
            bind = bind.replace("C-", "Ctrl+")\
                       .replace("A-", "Alt+")\
                       .replace("S-", "Shift+")

            qs = QShortcut(bind, display)
            qs.activated.connect(lambda d=display, f=func: f(d))
            qs.activatedAmbiguously.connect(
                lambda d=display, f=func: execute_if_focused(d, f)
            )
            yield qs
