# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QDockWidget, QLabel, QWidget


class Dock(QDockWidget):
    def __init__(self, title: str, parent: QWidget, title_bar: bool = False
                ) -> None:
        super().__init__(title, parent)
        self.title_bar:       TitleBar   = TitleBar(title, self)
        self.title_bar_shown: Optional[bool] = None
        self.show_title_bar(title_bar)

        # When e.g. user select the tab for this dock
        self.visibilityChanged.connect(self.on_visibility_change)
        self.dockLocationChanged.connect(self.on_location_change)


    def show_title_bar(self, show: Optional[bool] = None) -> None:
        if show is None:
            show = not self.title_bar_shown

        self.setTitleBarWidget(self.title_bar if show else QWidget())
        self.title_bar_shown = show


    def focus(self) -> None:
        self.show()
        self.raise_()


    def on_visibility_change(self, visible: bool) -> None:
        if visible:
            self.focus()


    def on_location_change(self, _: Qt.AllDockWidgetAreas) -> None:
        self.focus()


class TitleBar(QLabel):
    # pylint: disable=invalid-name
    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)

        if event.button() == Qt.MiddleButton:
            self.parent().hide()
