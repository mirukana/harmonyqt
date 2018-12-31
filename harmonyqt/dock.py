# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QDockWidget, QLabel, QWidget


class Dock(QDockWidget):
    def __init__(self,
                 title:              str,
                 parent:             QWidget,
                 can_hide_title_bar: bool = True,
                 show_title_bar:     bool = True) -> None:
        super().__init__(title, parent)
        self.current_area: Optional[Qt.DockWidgetArea] = None

        self.title_bar:          TitleBar = TitleBar(title, self)
        self.can_hide_title_bar: bool     = can_hide_title_bar
        self.title_bar_shown:    bool     = show_title_bar
        self.show_title_bar(show_title_bar)

        # When e.g. user select the tab for this dock
        self.visibilityChanged.connect(self.on_visibility_change)
        self.dockLocationChanged.connect(self.on_location_change)


    def show_title_bar(self, show: Optional[bool] = None) -> None:
        if not self.can_hide_title_bar:
            show = True

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


    def on_location_change(self, new_area: Qt.DockWidgetArea) -> None:
        self.current_area = new_area
        self.focus()


class TitleBar(QLabel):
    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)

        if event.button() == Qt.MiddleButton:
            self.parent().hide()
