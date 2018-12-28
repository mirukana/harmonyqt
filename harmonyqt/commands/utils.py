# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import shlex
from typing import Any, Callable

from ..chat import Chat


def str_arg_to_bool(string: str) -> bool:
    """Return True for 'true', 'yes', 'y', or '1'; False for 'false', 'no',
    'n', or '0'. Case-insensitive."""
    string = string.lower()
    yes    = ["true", "yes", "y", "1"]
    no     = ["false", "no", "n", "0"]

    if string in yes:
        return True
    if string in no:
        return False

    must = "must be one of: '%s'" % "', '".join(yes + no)
    raise ValueError(f"Cannot parse {string!r} as boolean - {must}")


def str_arg_to_list(string: str, values_converter: Callable[[str], Any] = str,
                   ) -> list:
    """Split string on commas, supporting shell-style quoting and escaping
    for values (e.g. `first,"second,thing",bar`).
    Values containing commas or whitespace must be quoted/escaped.
    values_converter is the function used to convert list elements before
    returning them; usually a type like bool, int, float or str."""

    if values_converter is bool:
        values_converter = str_arg_to_bool

    splitter                  = shlex.shlex(string, posix=True)
    splitter.whitespace      += ","
    splitter.whitespace_split = True
    values                    = list(splitter)

    return [values_converter(v) for v in values]


def expand_user(chat: Chat, user: str) -> str:
    return chat.client.user_id if user == "@" else user


def print_info(chat: Chat, markdown_text: str) -> None:
    chat.messages.system_print_request.emit(markdown_text, "info")

def print_warn(chat: Chat, markdown_text: str) -> None:
    chat.messages.system_print_request.emit(markdown_text, "warning")

def print_err(chat: Chat, markdown_text: str) -> None:
    chat.messages.system_print_request.emit(markdown_text, "error")
