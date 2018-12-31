# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import traceback
from typing import Callable, Optional

from ..chat import Chat


def print_info(chat: Chat, text: str, is_html: bool = False) -> None:
    chat.messages.system_print_request.emit(text, "info", is_html)


def print_warn(chat: Chat, text: str, is_html: bool = False) -> None:
    chat.messages.system_print_request.emit(text, "warning", is_html)


def print_err(chat: Chat, text: str, is_html: bool = False) -> None:
    chat.messages.system_print_request.emit(text, "error", is_html)


def print_exception(chat:     Chat,
                    err:      Exception,
                    bad_func: Optional[Callable] = None) -> None:
    traceback.print_exc()
    trace = traceback.format_exc().rstrip()
    shown = "".join((
        f"<code>{bad_func.__name__}</code>: " if bad_func else "",
        f"{type(err).__name__} - {err!s}<br><pre><code>{trace}</pre></code>",
    ))
    print_err(chat, shown, is_html=True)
