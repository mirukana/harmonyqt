# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from multiprocessing.pool import ThreadPool
from typing import Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFontMetrics, QKeyEvent, QResizeEvent
from PyQt5.QtWidgets import QGridLayout, QPlainTextEdit, QSizePolicy, QWidget

from . import Chat
from ..commands.eval import eval_f


class SendBox(QPlainTextEdit):
    def __init__(self, area: "SendArea") -> None:
        super().__init__()
        self.area  = area
        self._pool = ThreadPool(1)

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

        height = (widget_margin.top()    +
                  widget_margin.bottom() +
                  document_margin * 2    +
                  # Extra pixel prevents wordwrap-scroll-box-grows from hiding
                  # the first line
                  font_height * lines + 1)

        return min(height, self.area.chat.height() // 2)


    def sizeHint(self) -> QSize:
        return QSize(1, self.get_box_height())

    def minimumSizeHint(self) -> QSize:
        return QSize(1, self.get_box_height(lines=1))


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.updateGeometry()  # on main window resize, adjust max height


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
        text = self.toPlainText().rstrip()
        if not text:
            return

        self.clear()

        self._pool.apply_async(
            func           = eval_f,
            args           = (self.area.chat, text),
            error_callback = self.on_error
        )


    @staticmethod
    def on_error(err: BaseException) -> None:
        raise err


class SendArea(QWidget):
    def __init__(self, chat: Chat) -> None:
        super().__init__(chat)
        self.chat = chat

        self.grid = QGridLayout(self)
        self.original_margin = self.grid.contentsMargins()
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.box = SendBox(self)
        self.grid.addWidget(self.box, 0, 0)
