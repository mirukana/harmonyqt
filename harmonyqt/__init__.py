# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from pkg_resources import resource_filename

from .__about__ import __doc__
from . import __about__

with open(resource_filename(__about__.__name__, "stylesheet.qss"), "r") as ss:
    STYLESHEET = ss.read()

ICON_PACK = resource_filename(__about__.__name__, "icons/placeholder_white")

# pylint: disable=wrong-import-position
from . import (caches, dialogs,
               accounts, events, actions, chat, usertree,
               homepage, toolbar, main)
