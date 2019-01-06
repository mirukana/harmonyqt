# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import sys
from typing import Callable, List, Optional, Set

from pkg_resources import resource_filename
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow

from . import __about__, error_handler
# pylint: disable=redefined-builtin
from .__about__ import __doc__

StartupFuncType = Callable[[QApplication, QMainWindow], None]

_APP:               Optional[QApplication] = None
_MAIN_WINDOW:       Optional[QMainWindow]  = None
_STARTUP_FUNCTIONS: Set[StartupFuncType] = set()


def app() -> QApplication:
    if not _APP:
        raise RuntimeError("Application not initialized.")
    return _APP


def main_window() -> QMainWindow:
    if not _MAIN_WINDOW:
        raise RuntimeError("Main window not initialized.")
    return _MAIN_WINDOW


def register_startup_function(func: StartupFuncType) -> None:
    _STARTUP_FUNCTIONS.add(func)


def on_ctrl_c() -> None:
    try:
        main_window().normal_close = True
    except RuntimeError:
        pass


def run(argv: Optional[List[str]] = None) -> None:
    from . import main
    # pylint: disable=global-statement
    global _APP
    _APP = main.App(argv or sys.argv)

    global _MAIN_WINDOW
    _MAIN_WINDOW = main.MainWindow()
    _MAIN_WINDOW.construct()

    for func in _STARTUP_FUNCTIONS:
        func(_APP, _MAIN_WINDOW)

    # Make CTRL-C work
    timer = QTimer()
    timer.timeout.connect(on_ctrl_c)
    timer.start(100)

    sys.exit(_APP.exec_())
