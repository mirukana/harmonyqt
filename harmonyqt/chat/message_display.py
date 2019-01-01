# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import time
from threading import Thread
from typing import Deque, Tuple

from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import (
    QFontMetrics, QKeyEvent, QResizeEvent, QTextCursor, QTextFrameFormat,
    QTextLength, QTextTableFormat
)
from PyQt5.QtWidgets import QTextBrowser

from . import Chat
from .. import main_window, markdown, scroller
from ..message import Message


class MessageDisplay(QTextBrowser):
    _add_message_request = pyqtSignal(Message)
    # Useful for anything in a thread that wants to show text
    system_print_request = pyqtSignal(str, str, bool)  # text, level, is_html


    def __init__(self, chat: Chat) -> None:
        super().__init__()
        self.chat = chat

        self.scroller = scroller.Scroller(self)

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
        Message.local_echo_hooks["messageDisplay"] = self.on_receive_local_echo

        self.reached_history_end: bool = False
        self.history_token:       str  = ""

        Thread(target=self.autoload_history, daemon=True).start()

        self._add_message_request.connect(self._add_message)
        self.system_print_request.connect(self.system_print)

        self._set_previous_resize_vbar()
        self.scroller.vbar.valueChanged.connect(
            lambda _: self._set_previous_resize_vbar()
        )


    def _set_previous_resize_vbar(self) -> None:
        sc                         = self.scroller
        self._previous_resize_vbar = (sc.vmin, sc.v, sc.vmax)


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
        distance_from_left   = self.scroller.h
        distance_from_bottom = self.scroller.vmax - self.scroller.v

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
            self.scroller.hset(distance_from_left)\
                         .vset(self.scroller.vmax - distance_from_bottom)
        elif distance_from_bottom <= 10:
            self.scroller.go_min_left().go_bottom()


    def system_print(self,
                     text:    str,
                     level:   str  = "info",
                     is_html: bool = False) -> None:
        assert level in ("info", "warning", "error")
        distance_from_bottom = self.scroller.vmax - self.scroller.v

        html = text if is_html else markdown.to_html(text)
        html = f"<div class='system {level}'>{html}</div>"

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.End)
        cursor.insertFrame(self.system_print_frame_format)
        cursor.insertHtml(html)
        cursor.endEditBlock()

        if distance_from_bottom <= 10:
            self.scroller.go_min_left().go_bottom()


    def autoload_history(self) -> None:
        time.sleep(0.25)  # Give time for initial events/msgs to be shown
        scr = self.scroller

        while not self.reached_history_end:
            if self.isVisible():
                current = scr.v

                if scr.vmax <= scr.vstep_page:
                    self.load_one_history_chunk(msgs=25)

                elif current <= scr.vmin:
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


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if event.oldSize().height() < 0:
            return

        _, old_vbar_val, old_vbar_max = self._previous_resize_vbar
        scr = self.scroller
        scr.vset(scr.vmax - (old_vbar_max - old_vbar_val))


    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.modifiers() in (Qt.NoModifier, Qt.ShiftModifier):
            self.chat.send_area.box.setFocus()
            self.chat.send_area.box.keyPressEvent(event)
            return

        super().keyPressEvent(event)
