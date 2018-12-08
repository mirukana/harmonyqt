# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Callable, List, Optional, Sequence

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QGridLayout,
                             QLabel, QLineEdit, QMainWindow, QPushButton,
                             QSizePolicy, QSpacerItem, QWidget)

from .. import STYLESHEET, get_icon


class InfoLine(QLabel):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setProperty("error", False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.hide()


    def _set_to(self, text: Optional[str] = None) -> None:
        self.setText(text)
        if text:
            self.show()
        else:
            self.hide()

        # Reload CSS
        self.style().unpolish(self)
        self.style().polish(self)


    def clear(self) -> None:
        self.setProperty("error", False)
        self._set_to(None)


    def set_info(self, text: str) -> None:
        self.setProperty("error", False)
        self._set_to(text)


    def set_err(self, text: str) -> None:
        self.setProperty("error", True)
        self._set_to(text)


class Field(QWidget):
    def __init__(self,
                 parent:       QWidget,
                 label:        str,
                 placeholder : str  = "",
                 default_text: str  = "",
                 tooltip:      str  = "",
                 is_password:  bool = False) -> None:
        super().__init__(parent)

        self.grid = QGridLayout(self)

        self.label = QLabel(label, parent)
        self.grid.addWidget(self.label, 0, 0)

        self.line_edit = QLineEdit(parent)
        self.line_edit.setDragEnabled(True)
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setText(default_text)
        if is_password:
            self.line_edit.setEchoMode(QLineEdit.Password)
        self.grid.addWidget(self.line_edit, 1, 0)

        if tooltip:
            for obj in (self.label, self.line_edit):
                obj.setToolTip(tooltip)


class CheckBox(QCheckBox):
    def __init__(self,
                 parent: QWidget, text: str, tooltip: str, check: bool = False
                ) -> None:
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setChecked(check)


class ComboBox(QWidget):
    def __init__(self,
                 parent:  QWidget,
                 label:   str,
                 items:   List[str],
                 tooltip: str = "") -> None:
        super().__init__(parent)

        self.grid = QGridLayout(self)

        self.label = QLabel(label, parent)
        self.grid.addWidget(self.label, 0, 0)

        self.combo_box = QComboBox(parent)
        self.combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_box.setInsertPolicy(QComboBox.NoInsert)
        self.combo_box.setMinimumWidth(192)
        self.combo_box.addItems(items)
        self.grid.addWidget(self.combo_box, 0, 1)

        if tooltip:
            for obj in (self.label, self.combo_box):
                obj.setToolTip(tooltip)


class AcceptButton(QPushButton):
    def __init__(self,
                 dialog:          QDialog,
                 text:            str             = "&Accept",
                 on_click:        Optional[Callable[[bool], None]] = None,
                 required_fields: Sequence[Field] = ()) -> None:
        super().__init__(get_icon("accept_small.png"), text, dialog)
        self.dialog         = dialog
        self.text_in_fields = {}

        self.on_click = on_click if on_click else \
                        lambda _: self.dialog.done(0)

        self.setEnabled(not required_fields)

        # Button will be disabled until all these fields have a value:
        for field in required_fields:
            self.text_in_fields[field] = bool(field.line_edit.text())

            field.line_edit.textChanged.connect(
                lambda text, f=field: self.on_field_change(f, text)
            )

        self.clicked.connect(self.on_click)


    def on_field_change(self, field: str, text: str) -> None:
        self.text_in_fields[field] = bool(text)
        self.setEnabled(
            all((has_text for has_text in self.text_in_fields.values()))
        )


class CancelButton(QPushButton):
    def __init__(self, dialog: QDialog, text: str = "&Cancel") -> None:
        super().__init__(get_icon("cancel_small.png"), text, dialog)
        self.dialog = dialog
        self.clicked.connect(self.on_click)


    def on_click(self, _) -> None:
        self.dialog.done(1)


class GridDialog(QDialog):
    def __init__(self, main_window: QMainWindow, title: str) -> None:
        super().__init__(main_window)
        self.main_window = main_window

        self.setStyleSheet(STYLESHEET)
        self.setWindowTitle(f"Harmony - {title}")
        self.setWindowOpacity(0.9)

        self.grid = QGridLayout(self)


    def add_spacer(self, row: int, col: int) -> None:
        spc = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid.addItem(spc, row, col)


    def open_modeless(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()


class BlankLine(QWidget):
    pass
