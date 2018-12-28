# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import pdb as actual_pdb
import sys

# pylint: disable=no-name-in-module
from PyQt5.QtCore import pyqtRemoveInputHook

from . import register
from .utils import str_arg_to_bool


@register
def pdb(_, force: str = "no") -> None:
    """Enter the Python debugger (must be running from a terminal).
    If no attached terminal is detected, this command will abort to
    not freeze the program without any way of resuming,
    unless `force=yes` is used.
    """
    if not sys.stdin.isatty() and not str_arg_to_bool(force):
        raise RuntimeError("No attached terminal detected, see `/help pdb`.")

    pyqtRemoveInputHook()
    actual_pdb.set_trace()  # pylint: disable=no-member
