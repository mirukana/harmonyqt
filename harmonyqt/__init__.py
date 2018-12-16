# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import sys
from typing import List, Optional

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow

from .__about__ import __doc__
from . import __about__


_APP:         Optional[QApplication] = None
_MAIN_WINDOW: Optional[QMainWindow]  = None


def app() -> QApplication:
    if not _APP:
        raise RuntimeError("Application not initialized.")
    return _APP


def main_window() -> QMainWindow:
    if not _MAIN_WINDOW:
        raise RuntimeError("Main window not initialized.")
    return _MAIN_WINDOW


def run(argv: Optional[List[str]] = None) -> None:
    from . import main
    # pylint: disable=global-statement
    global _APP
    _APP = main.App(argv or sys.argv)

    global _MAIN_WINDOW
    _MAIN_WINDOW = main.MainWindow()
    _MAIN_WINDOW.construct()

    # Make CTRL-C work
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(_APP.exec_())
