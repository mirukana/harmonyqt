# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from threading import Thread
from typing import Deque, List, Tuple

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import (
    QFontMetrics, QTextCursor, QTextLength, QTextTableFormat
)
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window
from ..messages import Message


class MessageList(QTextBrowser):
    new_message_to_add_signal = pyqtSignal(Message)


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
            # QTextLength(QTextLength.FixedLength,    48),  # avatar
            QTextLength(QTextLength.FixedLength,    0),
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

        self.added_msgs_dates: Deque[int] = Deque()

        self.reached_history_end: bool = False
        self.history_token:       str  = ""

        # main_window().messages.signal.new_message.connect(self.add_message)
        Thread(target=self.autoload_history, daemon=True).start()


    def add_message(self, msg: Message) -> None:
        uid = self.chat.client.user_id
        try:
            index = self.local_echoed.index((uid, msg.html_content))
        except ValueError:
            pass
        else:
            del self.local_echoed[index]
            return

        sb                   = self.verticalScrollBar()
        distance_from_bottom = sb.maximum() - sb.value()

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()

        to_top = msg.was_created_before(self.start_ms_since_epoch)
        if to_top:
            cursor.movePosition(QTextCursor.Start)

            i = 0
            for i, date in enumerate(self.added_msgs_dates, i):
                if msg.ms_since_epoch < date:
                    self.added_msgs_dates.insert(i, msg.ms_since_epoch)
                    cursor.movePosition(QTextCursor.Down, n=i)
                    break
            else:
                self.added_msgs_dates.append(msg.ms_since_epoch)
                cursor.movePosition(QTextCursor.End)
        else:
            cursor.movePosition(QTextCursor.End)

        cursor.insertTable(1, 2, self.msg_table_format)
        # cursor.insertHtml(msg.html_avatar)
        cursor.movePosition(QTextCursor.NextBlock)

        cursor.insertTable(2, 1, self.inner_info_content_table_format)
        cursor.insertHtml(msg.html_info)
        cursor.movePosition(QTextCursor.NextBlock)
        cursor.insertHtml(msg.html_content)

        cursor.endEditBlock()

        if to_top:
            sb.setValue(sb.maximum() - distance_from_bottom)
        elif distance_from_bottom <= 10:
            sb.setValue(sb.maximum())


    def local_echo(self, text: str) -> None:
        uid = self.chat.client.user_id
        msg = Message(
            sender_id   = uid,
            receiver_id = uid,
            room_id     = self.chat.room.room_id,
            content     = text,
        )
        self.local_echoed.append((uid, msg.html_content))
        self.add_message(msg)


    def autoload_history(self) -> None:
        time.sleep(0.25)  # Give time for initial events/msgs to be shown
        sb = self.verticalScrollBar()

        while not self.reached_history_end:
            current = sb.value()

            if sb.maximum() <= sb.pageStep():
                self.load_one_history_chunk(msgs=25)

            elif current <= sb.minimum():
                self.load_one_history_chunk()

            time.sleep(0.1)


    def load_one_history_chunk(self, msgs: int = 100) -> None:
        assert 1 <= msgs <= 100  # matrix limit

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
            main_window().events.process_event(self.chat.client.user_id, event)
