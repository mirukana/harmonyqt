# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from threading import Event, Thread
from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextTableFormat
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window, accounts


class MessageList(QTextBrowser):
    new_message_from_queue_signal = pyqtSignal(dict, bool)


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        self.msg_tables_format = QTextTableFormat()
        self.msg_tables_format.setBorder(0)
        self.msg_tables_format.setBottomMargin(16)

        self.new_message_from_queue_signal.connect(self.add_message)
        self.queue_thread = Thread(target=self.process_queue, daemon=True)
        self.queue_thread.start()

        self._adding_history:     Event         = Event()
        self._ignored_events:     int           = 0
        self.reached_history_end: bool          = False
        self.history_token:       Optional[str] = None
        self.history_thread = Thread(target=self.load_history, daemon=True)
        # self.history_thread.start()


    def process_queue(self) -> None:
        user_id = self.chat.client.user_id
        room_id = self.chat.room.room_id
        msgs    = main_window().messages

        while True:
            try:
                queue = msgs[user_id][room_id]
                break
            except KeyError:
                time.sleep(0.1)

        while True:
            # [0] = timestamp (priority queue ordering key)
            msg = queue.get()[1]

            self.new_message_from_queue_signal.emit(msg, False)


    def add_message(self, msg: dict, to_top: bool = False) -> None:
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum()

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start if to_top else QTextCursor.End)

        msg_table  = cursor.insertTable(1, 2, self.msg_tables_format)
        msg_cursor = msg_table.cellAt(0, 1).lastCursorPosition()
        msg_cursor.insertHtml(msg["display"]["msg"])

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())


    def load_history(self) -> None:
        sbar = self.verticalScrollBar()

        while not self.reached_history_end:
            busy = self._adding_history.is_set()

            if not busy and sbar.value() <= sbar.minimum() + sbar.pageStep():
                Thread(target=self._load_history_chunk, daemon=True).start()

            time.sleep(0.1)


    def _load_history_chunk(self) -> None:
        self._adding_history.set()

        result = self.chat.client.api.get_room_messages(
            room_id   = self.chat.room.room_id,
            token     = self.history_token or self.chat.room.prev_batch,
            direction = "b",  # backward
            limit     = 50,
        )

        if result["end"] == self.history_token:
            self.reached_history_end = True
            return

        self.history_token = result["end"]
        print("History token:", result["end"])

        for event in result["chunk"]:
            if self._ignored_events <= accounts.LOAD_NUM_EVENTS_ON_START:
                self._ignored_events += 1
                continue

            self.new_message_from_queue_signal.emit(event, True)  # to_top

        self._adding_history.clear()
