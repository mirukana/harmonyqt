# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from collections import OrderedDict
from typing import Dict, List, Sequence, Set, Tuple

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QAction, QMenu, QWidget


class Menu(QMenu):
    def __init__(self, parent: QWidget, actions: Sequence[QAction] = ()
                ) -> None:
        super().__init__(parent)
        self.is_empty: bool = True

        self.setWindowOpacity(0.9)
        # self.setTearOffEnabled(True)
        self.setToolTipsVisible(True)

        if not actions:
            return

        # Auto-group "duplicate" actions
        # e.g. if two room rows are selected, show only one menu entry:
        # "Leave selected rooms"

        from .actions import Action, MultiselectAction

        seen_once: Dict[str, Action]       = {}
        groups:    Dict[str, List[Action]] = {}
        to_add:    List[Action]            = []

        for act in actions:
            ms_txt = getattr(act, "multiselect_text", None)

            if not ms_txt:
                continue

            if ms_txt not in seen_once:
                seen_once[ms_txt] = act
                continue

            if ms_txt not in groups:
                groups[ms_txt] = [seen_once[ms_txt]]

            groups[ms_txt].append(act)

        for acts in groups.values():
            to_add.append(MultiselectAction(acts))

        for act in actions:
            ms_txt = getattr(act, "multiselect_text", None)

            if not ms_txt or ms_txt not in groups:
                to_add.append(act)


        # Remove left duplicates: action without multiselect_text
        seen_once2: Set[Tuple[str, str]]          = set()
        to_add2:    Dict[Tuple[str, str], Action] = OrderedDict()

        for act in to_add:
            ident: Tuple[str, str] = (type(act).__name__, act.text)

            if ident in seen_once:
                to_add2.pop(ident, None)
                continue

            to_add2[ident] = act
            seen_once2.add(ident)

        if to_add2:
            self.is_empty = False
            self.addActions(to_add2.values())


    def exec_if_not_empty(self, position: QPoint) -> None:
        if not self.is_empty:
            self.exec_(position)
