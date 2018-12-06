# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Optional

from matrix_client.errors import (MatrixError, MatrixHttpLibError,
                                  MatrixRequestError)
# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QGridLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QSizePolicy,
                             QSpacerItem, QWidget)


class CreateRoom(QDialog):
    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window)
        self.main_window = main_window
