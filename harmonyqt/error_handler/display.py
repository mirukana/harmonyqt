# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv2.

from ..message_display import MessageDisplay


class ConsoleDisplay(MessageDisplay):
    def __init__(self) -> None:
        super().__init__()
        self.system_print_format.setTopMargin(self.font_height * 3)


    def print_error(self, trace_str: str, date: str) -> None:
        trace = trace_str.rstrip()
        self.system_print(
            f"<h3>{date}</h3><br><pre><code>{trace}</code></pre>",
            "error",
            is_html=True
        )
