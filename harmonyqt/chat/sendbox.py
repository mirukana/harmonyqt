# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from threading import Thread
from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFontMetrics, QKeyEvent
from PyQt5.QtWidgets import QPlainTextEdit, QSizePolicy

from . import Chat


class SendBox(QPlainTextEdit):
    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        self.setPlaceholderText("Send a message...")
        self.setCenterOnScroll(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.textChanged.connect(self.updateGeometry)


    def get_box_height(self, lines: Optional[int] = None) -> int:
        lines           = lines or self.document().lineCount()
        widget_margin   = self.contentsMargins()
        document_margin = self.document().documentMargin()
        font_height     = QFontMetrics(self.document().defaultFont()).height()

        return (widget_margin.top()    +
                widget_margin.bottom() +
                document_margin * 2    +
                font_height     * lines)

    # pylint: disable=invalid-name

    def sizeHint(self) -> QSize:
        return QSize(-1, self.get_box_height())

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
            self.chat.room.send_html(text)

        text = self.toPlainText()
        text = text.replace("\n", "<br>")
        if not text:
            return

        if text.startswith("/b"):
            try:
                limit = int(text.split()[1])
            except IndexError:
                limit = 10
            self.chat.room.backfill_previous_messages(limit=limit)
            return

        self.clear()

        # command escape
        if text.startswith("//") or text.startswith(r"\/"):
            Thread(target=do_it, args=(text[1:],)).start()

        elif text in ("/d",  "/debug"):
            import pdb
            from PyQt5.QtCore import pyqtRemoveInputHook
            pyqtRemoveInputHook()
            pdb.set_trace()  # pylint: disable=no-member

        elif text in ("/q", "/quit"):
            self.chat.parent().hide()

        else:
            Thread(target=do_it, args=(text,)).start()
