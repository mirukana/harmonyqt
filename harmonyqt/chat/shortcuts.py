# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Callable, Dict, Generator, List

from PyQt5.QtWidgets import QShortcut

from . import Chat


def _hscroll(chat: Chat, add_value: int, page: bool = False) -> None:
    hbar = chat.messages.horizontalScrollBar()
    step = hbar.pageStep() if page else hbar.singleStep()
    hbar.setValue(hbar.value() + add_value * step)

def _hedge(chat: Chat, right: bool) -> None:
    hbar = chat.messages.horizontalScrollBar()
    hbar.setValue(hbar.maximum() if right else hbar.minimum())

def _vscroll(chat: Chat, add_value: int, page: bool = False) -> None:
    vbar = chat.messages.verticalScrollBar()
    step = vbar.pageStep() if page else vbar.singleStep()
    vbar.setValue(vbar.value() + add_value * step)

def _vedge(chat: Chat, down: bool) -> None:
    vbar = chat.messages.verticalScrollBar()
    vbar.setValue(vbar.maximum() if down else vbar.minimum())


SHORTCUTS: Dict[Callable[[Chat], None], List[str]] = {
    # Alt+direction simple scroll
    lambda c: _hscroll(c, -1): ["A-h", "A-Left"],
    lambda c: _vscroll(c, +1): ["A-j", "A-Down"],
    lambda c: _vscroll(c, -1): ["A-k", "A-Up"],
    lambda c: _hscroll(c, +1): ["A-l", "A-Right"],

    # Ctrl+Alt+direction page scroll
    lambda c: _hscroll(c, -1, page=True): ["C-A-h", "C-A-Left"],
    lambda c: _vscroll(c, +1, page=True): ["C-A-j", "C-A-Down"],
    lambda c: _vscroll(c, -1, page=True): ["C-A-k", "C-A-Up"],
    lambda c: _hscroll(c, +1, page=True): ["C-A-l", "C-A-Right"],

    # Ctrl+Alt+Shift+direction begin/end scroll
    lambda c: _hedge(c, right=False): ["C-A-S-h", "C-A-S-Left"],
    lambda c: _vedge(c, down=True):   ["C-A-S-j", "C-A-S-Down"],
    lambda c: _vedge(c, down=False):  ["C-A-S-k", "C-A-S-Up"],
    lambda c: _hedge(c, right=True):  ["C-A-S-l", "C-A-S-Right"],
}


def get_shortcuts(chat: Chat) -> Generator[None, None, QShortcut]:
    for func, binds in SHORTCUTS.items():
        for bind in binds:
            bind = bind.replace("C-", "Ctrl+")\
                       .replace("A-", "Alt+")\
                       .replace("S-", "Shift+")

            qs = QShortcut(bind, chat)
            qs.activated.connect(lambda f=func, c=chat: f(c))
            yield qs
