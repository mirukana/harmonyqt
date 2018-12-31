# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QSizePolicy, QToolBar, QToolButton, QWidget, QWidgetAction
)

from . import __about__, actions, main_window, menu


class ActionsBar(QToolBar):
    button_visibility_changed_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(main_window())
        self.buttons: List[ActionButton] = []

        self.expand_button: QToolButton = self.children()[1]
        self.expand_button.setIcon(main_window().icons.icon("toolbar_expand"))
        self.expand_button.setProperty("is-expand-button", True)
        self.update_expand_menu()
        self.button_visibility_changed_signal.connect(self.update_expand_menu)

        acts = [actions.SetStatus, actions.AddAccount, actions.NewChat,
                actions.ToggleTitleBars, actions.Preferences]

        for action in acts:
            actwa = ActionWidget(self, action(main_window()))
            self.addAction(actwa)
            self.buttons.append(actwa.button)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)


    def update_expand_menu(self) -> None:
        # We need to handle this menu ourselves, else it will be made of
        # ActionButtons and not be a proper menu with shortcuts, submenus, etc.
        acts = [b.action for b in self.buttons if not b.isVisible()]
        self.expand_button.setMenu(menu.Menu(self, acts))


class ActionWidget(QWidgetAction):
    def __init__(self, bar: ActionsBar, action: actions.Action) -> None:
        super().__init__(bar)
        self.bar    = bar
        self.action = action
        self.button = ActionButton(self.bar, self.action)


    def createWidget(self, _: QWidget) -> int:
        return self.button

    @staticmethod
    def deleteWidget(widget: QWidget) -> None:
        # Original method deletes it from memory, causing expand menu to crash
        widget.hide()


class ActionButton(QToolButton):
    def __init__(self, bar: ActionsBar, action: actions.Action) -> None:
        super().__init__(bar)
        self.bar    = bar
        self.action = action

        self.setDefaultAction(self.action)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)


    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.bar.button_visibility_changed_signal.emit()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self.bar.button_visibility_changed_signal.emit()
