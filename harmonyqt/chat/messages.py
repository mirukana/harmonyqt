# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from threading import Thread
from typing import Deque, Tuple

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import (
    QFontMetrics, QResizeEvent, QTextCursor, QTextFrameFormat, QTextLength,
    QTextTableFormat
)
from PyQt5.QtWidgets import QTextBrowser

from . import Chat, markdown
from .. import main_window
from ..message import Message


class MessageList(QTextBrowser):
    _add_message_request = pyqtSignal(Message)
    # Useful for anything in a thread that wants to show text
    system_print_request = pyqtSignal(str, str, bool)  # text, level, is_html


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        doc = self.document()
        doc.setDefaultStyleSheet(main_window().theme.style("messages"))
        doc.setUndoRedoEnabled(False)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setOpenExternalLinks(True)

        top_margin = QFontMetrics(doc.defaultFont()).height()
        self.msg_table_format = QTextTableFormat()
        self.msg_table_format.setBorder(0)
        self.msg_table_format.setTopMargin(top_margin)
        self.msg_table_format.setColumnWidthConstraints([
            # QTextLength(QTextLength.FixedLength,    48),  # avatar
            QTextLength(QTextLength.FixedLength,    0),
            QTextLength(QTextLength.VariableLength, 0),   # info/content
        ])

        self.inner_info_content_table_format = QTextTableFormat()
        self.inner_info_content_table_format.setBorder(0)

        self.system_print_frame_format = QTextFrameFormat()
        self.system_print_frame_format.setBorder(0)
        self.system_print_frame_format.setTopMargin(top_margin)

        self.start_ms_since_epoch: int = \
            QDateTime.currentDateTime().toMSecsSinceEpoch()

        self.added_msgs_dates: Deque[int] = Deque()

        # [(msg.sender_id, msg.markdown)]
        self.received_by_local_echo: Deque[Tuple[str, str]] = Deque()
        Message.local_echo_hooks.append(self.on_receive_local_echo)

        self.reached_history_end: bool = False
        self.history_token:       str  = ""

        Thread(target=self.autoload_history, daemon=True).start()

        self._add_message_request.connect(self._add_message)
        self.system_print_request.connect(self.system_print)

        self._set_previous_resize_vbar()
        self.verticalScrollBar().valueChanged.connect(
            lambda _: self._set_previous_resize_vbar()
        )


    def _set_previous_resize_vbar(self) -> None:
        vb                         = self.verticalScrollBar()
        self._previous_resize_vbar = (vb.minimum(), vb.value(), vb.maximum())


    def on_receive_local_echo(self, msg: Message) -> None:
        if msg.room_id != self.chat.room.room_id:
            return

        msg.receiver_id = self.chat.client.user_id
        self.received_by_local_echo.append((msg.sender_id, msg.markdown))
        self._add_message_request.emit(msg)


    # Called from harmonyqt.chat.redirect_message()
    def on_receive_from_server(self, msg: Message) -> None:
        try:
            self.received_by_local_echo.remove((msg.sender_id, msg.markdown))
        except ValueError:  # not found in list/deque
            self._add_message_request.emit(msg)


    def _add_message(self, msg: Message) -> None:
        hbar                 = self.horizontalScrollBar()
        vbar                 = self.verticalScrollBar()
        distance_from_left   = hbar.value()
        distance_from_bottom = vbar.maximum() - vbar.value()

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
            hbar.setValue(distance_from_left)
            vbar.setValue(vbar.maximum() - distance_from_bottom)
        elif distance_from_bottom <= 10:
            hbar.setValue(hbar.minimum())
            vbar.setValue(vbar.maximum())


    def system_print(self,
                     text:    str,
                     level:   str  = "info",
                     is_html: bool = False) -> None:
        assert level in ("info", "warning", "error")
        hbar                 = self.horizontalScrollBar()
        vbar                 = self.verticalScrollBar()
        distance_from_bottom = vbar.maximum() - vbar.value()

        html = text if is_html else markdown.to_html(text)
        html = f"<div class='system {level}'>{html}</div>"

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.End)
        cursor.insertFrame(self.system_print_frame_format)
        cursor.insertHtml(html)
        cursor.endEditBlock()

        if distance_from_bottom <= 10:
            hbar.setValue(hbar.minimum())
            vbar.setValue(vbar.maximum())


    def autoload_history(self) -> None:
        time.sleep(0.25)  # Give time for initial events/msgs to be shown
        vbar = self.verticalScrollBar()

        while not self.reached_history_end:
            if self.isVisible():
                current = vbar.value()

                if vbar.maximum() <= vbar.pageStep():
                    self.load_one_history_chunk(msgs=25)

                elif current <= vbar.minimum():
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


    # pylint: disable=invalid-name
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if event.oldSize().height() < 0:
            return

        _, old_vbar_val, old_vbar_max = self._previous_resize_vbar
        vbar                          = self.verticalScrollBar()
        vbar.setValue(vbar.maximum() - (old_vbar_max - old_vbar_val))
