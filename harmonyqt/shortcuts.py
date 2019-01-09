# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from collections import Mapping
from typing import Callable, List, Optional, Set, Dict

from dataclasses import dataclass, field
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QShortcut, QWidget

from . import main_window

_KEEP_ALIVE: Set[QShortcut]  = set()


@dataclass(frozen=True)
class Shortcut:
    name:          str                = ""
    on_activation: Callable[[], None] = lambda: None
    bindings:      List[str]          = field(default_factory = list)
    autorepeat:    bool               = True
    parent:        Optional[QWidget]  = None
    context:       Qt.ShortcutContext = Qt.WindowShortcut


    def __post_init__(self) -> None:
        for bind in self.bindings:  # pylint: disable=not-an-iterable
            bind = bind.replace("C-", "Ctrl+")\
                        .replace("A-", "Alt+")\
                        .replace("S-", "Shift+")

            qs = QShortcut(bind, self.parent or main_window())
            qs.activated.connect(self.on_activation)  # type: ignore
            qs.setAutoRepeat(self.autorepeat)
            qs.setContext(self.context)
            _KEEP_ALIVE.add(qs)


class ShortcutManager(Mapping):
    def __init__(self) -> None:
        self._registered: Dict[str, Shortcut] = {}

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__, repr(self._registered))

    def __getitem__(self, key: str) -> Shortcut:
        return self._registered[key]

    def __iter__(self):
        return iter(self._registered)

    def __len__(self) -> int:
        return len(self._registered)


    def add(self, shortcut: Shortcut) -> None:
        self._registered[shortcut.name] = shortcut


    def remove(self, shortcut_name: str) -> None:
        del self._registered[shortcut_name]
