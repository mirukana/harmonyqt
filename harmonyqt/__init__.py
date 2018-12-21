# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import sys
from typing import Callable, List, Optional, Set

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow

from . import __about__
# pylint: disable=redefined-builtin
from .__about__ import __doc__

STARTUP_FUNC_TYPE = Callable[[QApplication, QMainWindow], None]

_APP:               Optional[QApplication] = None
_MAIN_WINDOW:       Optional[QMainWindow]  = None
_STARTUP_FUNCTIONS: Set[STARTUP_FUNC_TYPE] = set()


def app() -> QApplication:
    if not _APP:
        raise RuntimeError("Application not initialized.")
    return _APP


def main_window() -> QMainWindow:
    if not _MAIN_WINDOW:
        raise RuntimeError("Main window not initialized.")
    return _MAIN_WINDOW


def register_startup_function(func: STARTUP_FUNC_TYPE) -> None:
    _STARTUP_FUNCTIONS.add(func)


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
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(_APP.exec_())
