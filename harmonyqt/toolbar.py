# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import os

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QSizePolicy, QToolBar, QToolButton,
                             QWidget)

from . import __about__, actions

ICON_PACK = resource_filename(__about__.__name__, "icons/placeholder_white")


class ActionsBar(QToolBar):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window

        path = f"{ICON_PACK}{os.sep}toolbar_expand.png"
        self.children()[1].setIcon(QIcon(path))

        acts = [actions.SetStatus, actions.AddAccount, actions.NewChat,
                actions.ToggleTitleBars, actions.Preferences]

        for action in acts:
            self.add_spacer()                    # "distribute" items equally
            self.addAction(action(self.window))  # row, col
        self.add_spacer()

        for child in self.children():
            if isinstance(child, QToolButton):
                child.setPopupMode(QToolButton.InstantPopup)


    def add_spacer(self) -> QWidget:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)
        return spacer
