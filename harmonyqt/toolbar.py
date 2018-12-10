# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QSizePolicy, QToolBar, QToolButton, QWidget

from . import main_window, __about__, actions, get_icon


class ActionsBar(QToolBar):
    def __init__(self) -> None:
        super().__init__(main_window())

        self.setIconSize(QSize(24, 24))

        self.children()[1].setIcon(get_icon("toolbar_expand.png"))

        acts = [actions.SetStatus, actions.AddAccount, actions.NewChat,
                actions.ToggleTitleBars, actions.Preferences]

        for action in acts:
            self.add_spacer()  # "distribute" items equally
            self.addAction(action(main_window()))  # row, col
        self.add_spacer()

        for child in self.children():
            if isinstance(child, QToolButton):
                child.setPopupMode(QToolButton.InstantPopup)


    def add_spacer(self) -> QWidget:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)
        return spacer
