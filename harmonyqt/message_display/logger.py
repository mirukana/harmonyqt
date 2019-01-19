# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import logging
import traceback
from typing import Callable, Optional, Union

from .display import MessageDisplay


class DisplayLogger:
    def __init__(self, display: MessageDisplay) -> None:
        self.display:      MessageDisplay = display
        self.level:        int            = 0
        self.level_locked: bool           = False


    def debug(self, msg: str, *args, is_html: bool = False, **_) -> None:
        if self.level > logging.DEBUG:
            return
        self.display.system_print_request.emit(msg % args, "debug", is_html)


    def info(self, msg: str, *args, is_html: bool = False, **_) -> None:
        if self.level > logging.INFO:
            return
        self.display.system_print_request.emit(msg % args, "info", is_html)


    def warning(self, msg: str, *args, is_html: bool = False, **_) -> None:
        if self.level > logging.WARNING:
            return
        self.display.system_print_request.emit(msg % args, "warning", is_html)


    def error(self, msg: str, *args, is_html: bool = False, **_) -> None:
        if self.level > logging.ERROR:
            return
        self.display.system_print_request.emit(msg % args, "error", is_html)


    def critical(self, msg: str, *args, is_html: bool = False, **_) -> None:
        if self.level > logging.CRITICAL:
            return
        self.display.system_print_request.emit(msg % args, "critical", is_html)


    def exception(self, err: Exception, bad_func: Optional[Callable] = None
                 ) -> None:
        traceback.print_exc()
        trace = traceback.format_exc().rstrip()
        shown = "".join((
            f"<code>{bad_func.__name__}</code>: " if bad_func else "",

            f"{type(err).__name__} - {err!s}<br>"
            f"<pre><code>{trace}</pre></code>",
        ))
        self.error(shown, is_html=True)


    def setLevel(self, level: Union[int, str]) -> None:
        if self.level_locked:
            return

        if isinstance(level, str):
            level = getattr(logging, level.upper())

        assert isinstance(level, int)
        self.level = level
