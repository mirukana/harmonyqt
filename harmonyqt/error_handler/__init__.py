# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import atexit
import os
import sys
import threading
from traceback import format_exception, print_exc, print_exception
from types import TracebackType
from typing import List, Type

from atomicfile import AtomicFile
from PyQt5.QtCore import QDateTime, QObject, pyqtSignal

from ..__about__ import __email__
from ..utils import get_error_file

EMAIL         = __email__
URL_ISSUES    = "https://github.com/mirukan/harmonyqt/issues"
A_STYLE       = "style = 'color: rgb(40, 160, 110);'"
PLEASE_REPORT = (
    f"Please report problems, including this file, on "
    f"<a href='{URL_ISSUES}' {A_STYLE}>GitHub</a> or "
    f"by email to <a href='mailto:{EMAIL}' {A_STYLE}>{EMAIL}</a>."
)
LOG_PATH   = get_error_file()
WRITE_LOCK = threading.Lock()

# pylint: disable=wrong-import-position
from .console import Console

CAUGTH_EXCEPTION_MAY_EXIT: List[str] = []


def except_hook(type_:     Type[BaseException],
                value:     BaseException,
                traceback: TracebackType) -> None:

    if type_ is KeyboardInterrupt:
        sys.exit(130)

    print_exception(type_, value, traceback)

    trace_str = "\n".join(format_exception(type_, value, traceback))
    date      = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss.z t")

    add_to_log_file(trace_str, date)

    try:
        from .. import main_window
        window = main_window()

        if window.isVisible() and hasattr(window, "error_dock"):
            CAUGTH_EXCEPTION_MAY_EXIT.append(trace_str)
            window.show_error_dock()
            window.error_dock.widget().display.print_error(trace_str, date)
            return
    except Exception:
        print_exc()

    show_box(trace_str)


def add_to_log_file(trace_str: str, date: str) -> None:
    with WRITE_LOCK:
        mode = "a" if os.path.exists(LOG_PATH) else "w"
        with open(LOG_PATH, mode) as out_file:
            print("write", mode, LOG_PATH)
            out_file.write(f"{date}\n\n{trace_str}\n\n\n")


def show_box(trace_str: str) -> None:
    from . import boxes
    boxes.FatalErrorBox(trace_str).exec_()
    sys.exit(99)


@atexit.register
def error_box_if_console_exited():
    if not CAUGTH_EXCEPTION_MAY_EXIT:
        return

    err = CAUGTH_EXCEPTION_MAY_EXIT[-1]

    try:
        from .. import main_window
        normally_closed = main_window().normal_close
    except Exception:
        normally_closed = False

    if not normally_closed:
        show_box(trace_str=err)


class ExceptHookFromThreadCaller(QObject):
    call = pyqtSignal(tuple)

    def __init__(self):
        """https://stackoverflow.com/a/31622038
        Make `sys.excepthook` work in threads."""
        super().__init__()
        self.call.connect(lambda info: sys.excepthook(*info))
        real_self = self

        init_original = threading.Thread.__init__

        def init(self, *args, **kwargs):

            init_original(self, *args, **kwargs)
            run_original = self.run

            def run_with_except_hook(*args2, **kwargs2):
                try:
                    run_original(*args2, **kwargs2)
                except Exception:
                    real_self.call.emit(sys.exc_info())

            self.run = run_with_except_hook

        threading.Thread.__init__ = init


sys.excepthook = except_hook
_              = ExceptHookFromThreadCaller()
