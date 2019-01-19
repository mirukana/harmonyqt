# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from PyQt5.QtGui import QTextTableFormat

from ..message_display import MessageDisplay


class ConsoleDisplay(MessageDisplay):
    def __init__(self) -> None:
        super().__init__()
        self.error_format = QTextTableFormat()
        self.error_format.setBorder(0)
        self.error_format.setTopMargin(self.font_height * 3)


    def print_error(self, trace_str: str, date: str) -> None:
        trace = trace_str.rstrip()
        self.system_print(
            f"<h3>{date}</h3><br><pre><code>{trace}</code></pre>",
            level        = "error",
            is_html      = True,
            table_format = self.error_format,
        )
