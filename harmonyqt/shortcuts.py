# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

"Global keybinds"

from typing import Any, Callable, Dict, Generator, List

from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut

from . import app, main_window

SHORTCUTS: Dict[Callable[[QApplication, QMainWindow], Any], List[str]] = {
    # Focus changers
    lambda _, w: w.tree_dock.widget().setFocus(): ["A-a", "A-r"],
    lambda a, _: a.focused_chat_dock and a.focused_chat_dock.focus(): ["A-c"],
}


def get_shortcuts() -> Generator[None, None, QShortcut]:
    for func, binds in SHORTCUTS.items():
        for bind in binds:
            bind = bind.replace("C-", "Ctrl+")\
                       .replace("A-", "Alt+")\
                       .replace("S-", "Shift+")

            qs = QShortcut(bind, main_window())
            qs.activated.connect(
                lambda f=func, a=app(), w=main_window(): f(a, w)
            )
            yield qs
