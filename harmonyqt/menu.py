# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Dict, List, Sequence

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QAction, QMenu, QWidget


class Menu(QMenu):
    def __init__(self, parent: QWidget, actions: Sequence[QAction] = ()
                ) -> None:
        super().__init__(parent)
        self.setWindowOpacity(0.9)
        self.setTearOffEnabled(True)
        self.setToolTipsVisible(True)

        if not actions:
            return

        # Auto-group "duplicate" actions
        # e.g. if two room rows are selected, show only one menu entry:
        # "Leave selected rooms"

        from .actions import Action, MultiselectAction

        seen_once: Dict[str, Action]       = {}
        groups:    Dict[str, List[Action]] = {}

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
            self.addAction(MultiselectAction(acts))

        for act in actions:
            ms_txt = getattr(act, "multiselect_text", None)

            if not ms_txt or ms_txt not in groups:
                self.addAction(act)
