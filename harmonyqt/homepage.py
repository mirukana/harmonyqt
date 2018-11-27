# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class HomePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.build()


    def build(self) -> None:
        label = QLabel("Home page")
        self.vbox = QVBoxLayout(self)
        self.vbox.addWidget(label, alignment=Qt.AlignCenter)
