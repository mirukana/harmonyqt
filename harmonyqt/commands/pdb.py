# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import pdb as actual_pdb

from PyQt5.QtCore import pyqtRemoveInputHook

from . import register


@register(run_in_thread=False)
def pdb(*_) -> None:
    """Usage: /pdb

    Enter the Python debugger. Harmony must be running from a terminal."""
    pyqtRemoveInputHook()
    actual_pdb.set_trace()  # pylint: disable=no-member
