# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import pdb as actual_pdb

from PyQt5.QtCore import pyqtRemoveInputHook

from . import register
from .. import main_window, app
from ..chat import Chat


@register(run_in_thread=False)
def pdb(ch: Chat, _) -> None:
    """Usage: /pdb

    Enter the Python debugger. Harmony must be running from a terminal."""

    ap = app()
    wi = main_window()
    print("[App]        ap =", ap)
    print("[MainWindow] wi =", wi)
    print("[Chat]       ch =", ch)

    pyqtRemoveInputHook()
    actual_pdb.set_trace()  # pylint: disable=no-member
