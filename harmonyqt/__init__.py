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


_MAIN_WINDOW: Optional[QMainWindow] = None

def main_window() -> QMainWindow:
    if not _MAIN_WINDOW:
        raise RuntimeError("Main window not initialized.")
    return _MAIN_WINDOW


def run(argv: Optional[List[str]] = None) -> None:
    app = QApplication(argv or sys.argv)

    from .main import HarmonyQt
    # pylint: disable=global-statement
    global _MAIN_WINDOW
    _MAIN_WINDOW = HarmonyQt()
    _MAIN_WINDOW.construct()

    # Make CTRL-C work
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec_())
