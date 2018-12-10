# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from threading import Event, Lock, Thread
from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextTableFormat
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window, accounts


class MessageList(QTextBrowser):
    add_message_signal = pyqtSignal(dict, dict, bool)


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        self.msg_tables_format = QTextTableFormat()
        self.msg_tables_format.setBorder(0)
        self.msg_tables_format.setBottomMargin(16)

        self._lock: Lock = Lock()
        self.add_message_signal.connect(self._add_msg)
        self.queue_thread = Thread(target=self.process_events, daemon=True)
        self.queue_thread.start()

        self._adding_history:     Event         = Event()
        self._ignored_events:     int           = 0
        self.reached_history_end: bool          = False
        self.history_token:       Optional[str] = None
        self.history_thread = Thread(target=self.load_history, daemon=True)
        self.history_thread.start()


    # pylint: disable=invalid-name
    def updateGeometries(self) -> None:
        # Smoother scrolling when user e.g. clicks scrollbar arrows
        super().updateGeometries()
        self.verticalScrollBar().setSingleStep(2)


    def process_events(self) -> None:
        user_id = self.chat.client.user_id
        room_id = self.chat.room.room_id

        while True:
            try:
                msg = main_window().events.messages[user_id][room_id].get()
            except KeyError:
                time.sleep(0.05)
            else:
                Thread(target = self.add_message,
                       args   = (msg,),
                       daemon = True).start()


    def add_message(self, msg: dict, to_top: bool = False) -> None:
        with self._lock:  # Ensures messages are posted in the right order
            dispname = self.chat.room.members_displaynames.get(msg["sender"])

            if not dispname:
                known_users = self.chat.client.users
                for other_client in main_window().accounts.values():
                    known_users.update(other_client.users)

                user     = known_users.get(msg["sender"])
                dispname = user.get_display_name() if user else msg["sender"]

            extra    = {
                "name":      dispname,
                "date_time": QDateTime.\
                             fromMSecsSinceEpoch(msg["origin_server_ts"])
            }
            self.add_message_signal.emit(msg, extra, to_top)


    def _add_msg(self, event: dict, extra: dict, to_top: bool = False) -> None:
        display_name = extra["name"]
        datetime     = extra["date_time"].toString("HH:mm:ss")
        content      = event["content"]
        html         = content.get("formatted_body")
        plain        = content.get("body")

        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum()

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start if to_top else QTextCursor.End)

        msg_table = cursor.insertTable(1, 2, self.msg_tables_format)
        # img_cell  = msg_table.cellAt(1, 1)
        msg_cursor = msg_table.cellAt(0, 1).lastCursorPosition()


        if html:
            msg_cursor.insertHtml(f"{display_name} &nbsp;{datetime}<br>{html}")
        elif plain:
            msg_cursor.insertText(f"{display_name}  {datetime}\n{plain}")

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

            Thread(target = self.add_message,
                   kwargs = {"msg": event, "to_top": True},
                   daemon = True).start()

        self._adding_history.clear()
