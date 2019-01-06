# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import traceback
from typing import List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (
    QFontMetrics, QResizeEvent, QTextCursor, QTextTableFormat
)
from PyQt5.QtWidgets import QShortcut, QTextBrowser, QWidget

from . import shortcuts
from ..scroller import Scroller


class MessageDisplay(QTextBrowser):
    # Useful for anything in a thread that wants to show text
    system_print_request = pyqtSignal(str, str, bool)  # text, level, is_html


    def __init__(self) -> None:
        super().__init__()

        self.scroller = Scroller(self)
        self._set_previous_resize_vbar()
        self.scroller.vbar.valueChanged.connect(
            lambda _: self._set_previous_resize_vbar()
        )

        self.shortcuts: List[QShortcut] = list(shortcuts.get_shortcuts(self))

        doc = self.document()
        doc.setUndoRedoEnabled(False)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        self.font_height         = QFontMetrics(doc.defaultFont()).height()
        self.system_print_format = QTextTableFormat()
        self.system_print_format.setBorder(0)
        self.system_print_format.setTopMargin(self.font_height)

        self.system_print_request.connect(self.system_print)


    def apply_style(self) -> None:
        try:
            from harmonyqt import main_window
            window = main_window()
            doc    = self.document()
            doc.setDefaultStyleSheet(window.theme.style("messages"))
        except Exception:
            traceback.print_exc()


    def _set_previous_resize_vbar(self) -> None:
        sc                         = self.scroller
        self._previous_resize_vbar = (sc.vmin, sc.v, sc.vmax)


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if event.oldSize().height() < 0:
            return

        _, old_vbar_val, old_vbar_max = self._previous_resize_vbar
        scr = self.scroller
        scr.vset(scr.vmax - (old_vbar_max - old_vbar_val))


    def system_print(self,
                     text:    str,
                     level:   str  = "info",
                     is_html: bool = False) -> None:
        assert level in ("info", "warning", "error")
        distance_from_bottom = self.scroller.vmax - self.scroller.v

        html = text

        if not is_html:
            try:
                from harmonyqt import markdown
                html = markdown.to_html(text)
            except Exception:
                traceback.print_exc()

        html = f"<div class='system {level}'>{html}</div>"

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.End)
        cursor.insertTable(1, 1, self.system_print_format)
        cursor.insertHtml(html)
        cursor.endEditBlock()

        if distance_from_bottom <= 10:
            self.scroller.go_min_left().go_bottom()


    def make_shortcuts_accessible_from(self, widget: QWidget) -> None:
        widget.shortcuts = self.shortcuts.copy()
        self.shortcuts   = []
