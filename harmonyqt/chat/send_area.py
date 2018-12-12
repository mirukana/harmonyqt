# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFontMetrics, QKeyEvent
from PyQt5.QtWidgets import QGridLayout, QPlainTextEdit, QSizePolicy, QWidget

from . import Chat


class SendBox(QPlainTextEdit):
    def __init__(self, area: "SendArea") -> None:
        super().__init__()
        self.area = area
        self._pool  = ThreadPool(1)  # 1 to keep message sending order

        self.setPlaceholderText("Send a message…")
        self.setCenterOnScroll(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.document().setDocumentMargin(0)

        self.textChanged.connect(self.updateGeometry)


    def get_box_height(self, lines: Optional[int] = None) -> int:
        lines           = lines or self.document().lineCount()
        widget_margin   = self.contentsMargins()
        document_margin = self.document().documentMargin()
        font_height     = QFontMetrics(self.document().defaultFont()).height()

        return (widget_margin.top()    +
                widget_margin.bottom() +
                document_margin * 2    +
                # Extra pixel prevents wordwrap-scroll-box-grows from hiding
                # the first line
                font_height * lines + 1)

    # pylint: disable=invalid-name

    def sizeHint(self) -> QSize:
        return QSize(1, self.get_box_height())

    def minimumSizeHint(self) -> QSize:
        return QSize(1, self.get_box_height(lines=1))


    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):  # Enter = keypad
            if event.modifiers() in (Qt.NoModifier, Qt.KeypadModifier):
                if not event.isAutoRepeat():
                    self.send()
            else:
                self.insertPlainText("\n")  # Make it work with Shift/Alt/Ctrl
            return

        super().keyPressEvent(event)


    def send(self) -> None:
        def do_it(text: str) -> None:
            self.area.chat.room.send_html(text)

        text = self.toPlainText()
        text = text.replace("\n", "<br>")
        if not text:
            return

        self.clear()

        # command escape
        if text.startswith("//") or text.startswith(r"\/"):
            self._pool.apply_async(do_it, (text[1:],))

        elif text in ("/d",  "/debug"):
            import pdb
            from PyQt5.QtCore import pyqtRemoveInputHook
            pyqtRemoveInputHook()
            pdb.set_trace()  # pylint: disable=no-member

        elif text in ("/q", "/quit"):
            self.area.chat.parent().hide()

        else:
            self._pool.apply_async(do_it, (text,))


class SendArea(QWidget):
    def __init__(self, chat: Chat) -> None:
        super().__init__(chat)
        self.chat = chat

        self.grid = QGridLayout(self)
        self.original_margin = self.grid.contentsMargins()
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.box = SendBox(self)
        self.grid.addWidget(self.box, 0, 0)
