# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import os

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtGui import QIcon

from .__about__ import __doc__
from . import __about__

with open(resource_filename(__about__.__name__, "stylesheet.qss"), "r") as ss:
    STYLESHEET = ss.read()

ICON_PACK = resource_filename(__about__.__name__, "icons/placeholder_white")

def get_icon(filename: str) -> QIcon:
    return QIcon(f"{ICON_PACK}{os.sep}{filename}")


# pylint: disable=wrong-import-position
from . import (dialogs,
               accounts, events, actions, chat, usertree,
               homepage, toolbar, main, menu)
