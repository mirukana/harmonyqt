# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Any, Callable, Dict, List, Tuple

from harmonyqt import app, main, shortcuts

from .scroller import Scroller

SHORTCUTS: Dict[str, Tuple[Callable[[Scroller], Any], List[str]]] = {
    # Alt+direction simple scroll
    "left":  (lambda s: s.go_left(),  ["A-h", "A-Left"]),
    "down":  (lambda s: s.go_down(),  ["A-j", "A-Down"]),
    "up":    (lambda s: s.go_up(),    ["A-k", "A-Up"]),
    "right": (lambda s: s.go_right(), ["A-l", "A-Right"]),

    # Ctrl+Alt+direction page scroll
    "page left":  (lambda s: s.go_page_left(),  ["C-A-h", "C-A-Left"]),
    "page down":  (lambda s: s.go_page_down(),  ["C-A-j", "C-A-Down"]),
    "page up":    (lambda s: s.go_page_up(),    ["C-A-k", "C-A-Up"]),
    "page right": (lambda s: s.go_page_right(), ["C-A-l", "C-A-Right"]),

    # Ctrl+Alt+Shift+direction begin/end scroll
    "to left edge":  (lambda s: s.go_min_left(),  ["C-A-S-h", "C-A-S-Left"]),
    "to bottom":     (lambda s: s.go_bottom(),    ["C-A-S-j", "C-A-S-Down"]),
    "to top":        (lambda s: s.go_top(),       ["C-A-S-k", "C-A-S-Up"]),
    "to right edge": (lambda s: s.go_max_right(), ["C-A-S-l", "C-A-S-Right"]),
}


def register(window) -> None:
    for name, (func, binds) in SHORTCUTS.items():

        def on_activation(func = func) -> None:
            widget = app().get_focused(lambda w: hasattr(w, "scroller"))
            if widget is not None:
                func(widget.scroller)

        window.shortcuts.add(shortcuts.Shortcut(
            name          = f"Scroll {name}",
            on_activation = on_activation,
            bindings      = binds,
        ))


main.HOOKS_INIT_2_BEFORE_LOGIN["Register Scroller shortcuts"] = register
