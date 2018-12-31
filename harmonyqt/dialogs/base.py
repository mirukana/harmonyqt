# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from typing import Callable, Dict, Optional, Sequence

from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QGridLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem, QWidget
)

from .. import main_window


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
                 is_password:  bool = False,
                 lines:        int  = 1) -> None:
        super().__init__(parent)
        assert lines >= 1
        self.lines = lines

        self.grid = QGridLayout(self)

        self.label = QLabel(label, parent)
        self.grid.addWidget(self.label, 0, 0)

        if self.lines == 1:
            self.text_edit = QLineEdit(parent)
            self.text_edit.setDragEnabled(True)
            if is_password:
                self.text_edit.setEchoMode(QLineEdit.Password)
        else:
            self.text_edit = QPlainTextEdit(parent)
            self.text_edit.setTabChangesFocus(True)

            doc         = self.text_edit.document()
            doc_margins = doc.documentMargin()
            margins     = self.text_edit.contentsMargins()
            frame_width = self.text_edit.frameWidth()
            font_height = QFontMetrics(doc.defaultFont()).lineSpacing()
            self.text_edit.setFixedHeight((1 + self.lines) * font_height +
                                          (frame_width + doc_margins) * 2 +
                                          margins.top() + margins.bottom())

        self.text_edit.setPlaceholderText(placeholder)
        self.set_text(default_text)
        self.grid.addWidget(self.text_edit, 1, 0)

        if tooltip:
            for obj in (self.label, self.text_edit):
                obj.setToolTip(tooltip)


    def get_text(self) -> str:
        try:
            return self.text_edit.text()
        except AttributeError:
            return self.text_edit.toPlainText()

    def set_text(self, text: str) -> None:
        try:
            self.text_edit.setText(text)
        except AttributeError:
            self.text_edit.setPlainText(text)


class CheckBox(QCheckBox):
    def __init__(self,
                 parent: QWidget, text: str, tooltip: str, check: bool = False
                ) -> None:
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setChecked(check)


class ComboBox(QWidget):
    def __init__(self,
                 parent:       QWidget,
                 label:        str,
                 tooltip:      str           = "",
                 items:        Sequence[str] = (),
                 initial_item: str           = "") -> None:
        super().__init__(parent)

        self.grid = QGridLayout(self)

        self.label = QLabel(label, parent)
        self.grid.addWidget(self.label, 0, 0)

        self.combo_box = QComboBox(parent)
        self.combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_box.setInsertPolicy(QComboBox.NoInsert)
        self.combo_box.setMinimumWidth(192)
        self.combo_box.addItems(list(items))
        self.grid.addWidget(self.combo_box, 0, 1)

        if tooltip:
            for obj in (self.label, self.combo_box):
                obj.setToolTip(tooltip)

        if initial_item:
            self.select_item_with_text(initial_item)


    def del_items_with_text(self, text: str) -> int:
        deleted = 0
        for i in range(self.combo_box.count()):
            if self.combo_box.itemText(i) == text:
                self.combo_box.removeItem(i)
                deleted += 1
        return deleted


    def select_item_with_text(self, text: str) -> bool:
        for i in range(self.combo_box.count()):
            if self.combo_box.itemText(i) == text:
                self.combo_box.setCurrentIndex(i)
                return True
        return False


class AcceptButton(QPushButton):
    def __init__(self,
                 dialog:          QDialog,
                 text:            str             = "&Accept",
                 on_click:        Optional[Callable[[bool], None]] = None,
                 required_fields: Sequence[Field] = ()) -> None:
        super().__init__(main_window().icons.icon("accept_small"),
                         text, dialog)

        self.dialog:         QDialog           = dialog
        self.text_in_fields: Dict[Field, bool] = {}

        self.on_click = on_click if on_click else \
                        lambda _: self.dialog.done(0)

        self.setEnabled(not required_fields)

        # Button will be disabled until all these fields have a value:
        for field in required_fields:
            self.text_in_fields[field] = bool(field.get_text())

            field.text_edit.textChanged.connect(
                lambda text, f=field: self.on_field_change(f, text)
            )

        self.clicked.connect(self.on_click)


    def on_field_change(self, field: Field, text: str) -> None:
        self.text_in_fields[field] = bool(text)
        self.setEnabled(
            all((has_text for has_text in self.text_in_fields.values()))
        )


class CancelButton(QPushButton):
    def __init__(self, dialog: QDialog, text: str = "&Cancel") -> None:
        super().__init__(main_window().icons.icon("cancel_small"),
                         text, dialog)

        self.dialog = dialog
        self.clicked.connect(self.on_click)


    def on_click(self, _) -> None:
        self.dialog.done(1)


class GridDialog(QDialog):
    def __init__(self, title: str = "") -> None:
        super().__init__(main_window())

        self.setStyleSheet(main_window().theme.style("interface"))
        self.setWindowTitle(" - ".join(("Harmony", title)))
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
