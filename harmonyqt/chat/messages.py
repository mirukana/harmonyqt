# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import time
from queue import PriorityQueue
from threading import Thread
from typing import Dict

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextTableFormat
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window

MESSAGE_FILTERS: Dict[str, str] = {
    # Qt only knows <s> for striketrough
    r"(</?)\s*(del|strike)>": r"\1s>",
}


class MessageList(QTextBrowser):
    new_message_from_queue_signal = pyqtSignal(dict)


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        uid, rid = self.chat.client.user_id, self.chat.room.room_id
        while True:
            try:
                self.old_queue = main_window().messages.old[uid][rid]
                self.new_queue = main_window().messages.new[uid][rid]
                break
            except KeyError:
                time.sleep(0.05)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        self.msg_tables_format = QTextTableFormat()
        self.msg_tables_format.setBorder(0)
        self.msg_tables_format.setBottomMargin(16)

        self.new_message_from_queue_signal.connect(self.add_message)

        self.old_queue_thread = Thread(
            target=self.process_queue, args=(self.old_queue,), daemon=True
        )
        self.old_queue_thread.start()

        self.new_queue_thread = Thread(
            target=self.process_queue, args=(self.new_queue,), daemon=True
        )
        self.new_queue_thread.start()

        self._ignored_events:     int  = 0
        self.reached_history_end: bool = False
        self.history_token:       str  = ""

        self.history_thread = Thread(target=self.autoload_history, daemon=True)
        self.history_thread.start()


    def process_queue(self, queue: PriorityQueue) -> None:
        while True:
            event = queue.get()
            # [0]: timestamp, negated if old queue (priority ordering key)
            self.new_message_from_queue_signal.emit(event[1])


    def add_message(self, msg: dict) -> None:
        to_top = msg["display"]["is_from_past"]

        sb = self.verticalScrollBar()

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start if to_top else QTextCursor.End)

        distance_from_bottom = sb.maximum() - sb.value()

        msg_table  = cursor.insertTable(1, 2, self.msg_tables_format)
        msg_cursor = msg_table.cellAt(0, 1).lastCursorPosition()
        msg_cursor.insertHtml(self.filter_msg_content((msg["display"]["msg"])))

        if to_top or distance_from_bottom == 0:
            sb.setValue(sb.maximum() - distance_from_bottom)


    def autoload_history(self, chunk_msgs: int = 50) -> None:
        sb = self.verticalScrollBar()

        while not self.reached_history_end:
            current = sb.value()

            if current <= sb.minimum() or sb.maximum() <= sb.pageStep():
                self.load_one_history_chunk(chunk_msgs)

            # time.sleep(0.1)


    def load_one_history_chunk(self, msgs: int = 50) -> None:
        result = self.chat.client.api.get_room_messages(
            room_id   = self.chat.room.room_id,
            token     = self.history_token or self.chat.room.prev_batch,
            direction = "b",  # backward
            limit     = msgs,
        )

        if result["end"] == self.history_token:
            self.reached_history_end = True
            print("END")
            return

        self.history_token = result["end"]
        print("History token:", result["end"])

        for event in result["chunk"]:
            if event["type"] == "m.room.message":
                main_window().messages.on_new_message(
                    user_id      = self.chat.client.user_id,
                    room_id      = self.chat.room.room_id,
                    event        = event,
                    is_from_past = True
                )


    @staticmethod
    def filter_msg_content(content: str) -> str:  # content: HTML
        for regex, repl in MESSAGE_FILTERS.items():
            content = re.sub(regex, repl, content, re.IGNORECASE, re.MULTILINE)
        return content
