# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import time
from queue import PriorityQueue
from threading import Thread
from typing import Dict, List, Optional, Tuple

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import (
    QFontMetrics, QTextCursor, QTextLength, QTextTableFormat
)
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window
from ..messages import Message

MESSAGE_FILTERS: Dict[str, str] = {
    # Qt only knows <s> for striketrough
    r"(</?)\s*(del|strike)>": r"\1s>",
}


class MessageList(QTextBrowser):
    new_message_from_queue_signal = pyqtSignal(Message)


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        doc = self.document()
        doc.setDefaultStyleSheet(main_window().theme.style("messages"))
        doc.setUndoRedoEnabled(False)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        self.msg_table_format = QTextTableFormat()
        self.msg_table_format.setBorder(0)
        self.msg_table_format.setTopMargin(
            QFontMetrics(doc.defaultFont()).height()
        )
        self.msg_table_format.setColumnWidthConstraints([
            QTextLength(QTextLength.FixedLength,    48),  # avatar
            QTextLength(QTextLength.VariableLength, 0),   # info/content
        ])

        self.inner_info_content_table_format = QTextTableFormat()
        self.inner_info_content_table_format.setBorder(0)

        self.start_ms_since_epoch: int = \
            QDateTime.currentDateTime().toMSecsSinceEpoch()

        # Messages that have been already shown localy, without
        # waiting for the server's response.
        # [(user_id, html content)] - Can't use a set, we need "duplicates"
        self.local_echoed: List[Tuple[str, str]] = []

        self._queue: Optional[PriorityQueue] = None
        self.new_message_from_queue_signal.connect(self.add_message)

        self._ignored_events:     int  = 0
        self.reached_history_end: bool = False
        self.history_token:       str  = ""

        Thread(target=self.process_queue,    daemon=True).start()
        Thread(target=self.autoload_history, daemon=True).start()


    @property
    def queue(self) -> Optional[PriorityQueue]:
        if not self._queue:
            uid, rid = self.chat.client.user_id, self.chat.room.room_id
            try:
                self._queue = main_window().messages[uid][rid]
            except KeyError:
                return None

        return self._queue


    def process_queue(self) -> None:
        while not self.queue:
            time.sleep(0.1)

        while True:
            item: Tuple[int, Message] = self.queue.get()  # (timestamp, msg)

            lecho_val = (self.chat.client.user_id, item[1].html_content)
            try:
                index = self.local_echoed.index(lecho_val)
            except ValueError:
                pass
            else:
                del self.local_echoed[index]
                continue

            self.new_message_from_queue_signal.emit(item[1])


    def add_message(self, msg: Message) -> None:
        sb                   = self.verticalScrollBar()
        distance_from_bottom = sb.maximum() - sb.value()

        to_top = msg.was_created_before(self.start_ms_since_epoch)

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()

        cursor.movePosition(QTextCursor.Start if to_top else QTextCursor.End)

        cursor.insertTable(1, 2, self.msg_table_format)
        cursor.insertHtml(msg.html_avatar)
        cursor.movePosition(QTextCursor.NextBlock)

        cursor.insertTable(2, 1, self.inner_info_content_table_format)
        cursor.insertHtml(msg.html_info)
        cursor.movePosition(QTextCursor.NextBlock)
        cursor.insertHtml(self.filter_msg_content(msg.html_content))

        cursor.endEditBlock()

        if to_top or distance_from_bottom == 0:
            sb.setValue(sb.maximum() - distance_from_bottom)


    def local_echo(self, text: str) -> None:
        uid = self.chat.client.user_id
        msg = Message(uid, uid, self.chat.room.room_id, text)
        self.local_echoed.append((uid, msg.html_content))
        self.new_message_from_queue_signal.emit(msg)


    def autoload_history(self) -> None:
        time.sleep(0.25)
        sb = self.verticalScrollBar()

        while not self.reached_history_end:
            current = sb.value()

            if sb.maximum() <= sb.pageStep():
                self.load_one_history_chunk(msgs=20)

            elif current <= sb.minimum():
                self.load_one_history_chunk()
                time.sleep(0.25)


    def load_one_history_chunk(self, msgs: int = 100) -> None:
        assert msgs <= 100  # matrix limit

        result = self.chat.client.api.get_room_messages(
            room_id   = self.chat.room.room_id,
            token     = self.history_token or self.chat.room.prev_batch,
            direction = "b",  # backward
            limit     = msgs,
        )

        if result["end"] == self.history_token:
            self.reached_history_end = True
            return

        self.history_token = result["end"]

        for event in result["chunk"]:
            if event["type"] == "m.room.message":
                main_window().messages.on_new_message(self.chat.client.user_id,
                                                      event)


    @staticmethod
    def filter_msg_content(content: str) -> str:  # content: HTML
        for regex, repl in MESSAGE_FILTERS.items():
            content = re.sub(regex, repl, content, re.IGNORECASE, re.MULTILINE)
        return content
