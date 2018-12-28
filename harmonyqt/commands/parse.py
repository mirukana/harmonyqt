# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import shlex
import traceback as m_traceback
from typing import Dict, List

from . import REGISTERED_COMMANDS, register, utils
from ..chat import Chat


@register
def parse(chat: Chat, command: str, traceback: str = "no") -> None:
    """Evaluate and run `command`, default is `/say` if no *`/cmd`* specified.
    Errors only show a short message by default, use `traceback=yes` to
    print debugging details too.

    Examples:

        /parse Hi!
        /parse "/help full=yes"
        /parse "/parse '/badcommand'" traceback=yes
    """
    show_traceback = utils.str_arg_to_bool(traceback)

    ignore_cmd = command.startswith("//") or command.startswith(r"\/")

    if command.startswith("///") or command.startswith(r"\\/"):
        command = command[1:]

    if ignore_cmd or not command.startswith("/"):
        func, literal_args = "/say", [re.sub(r"(['\"=])", r"\\\1", command)]
    else:
        splitter                  = shlex.shlex(command, posix=True)
        splitter.whitespace_split = True
        func, *literal_args       = list(splitter)

    try:
        actual_func = REGISTERED_COMMANDS[func.lstrip("/")]
    except KeyError:
        rest = " …" if literal_args else ""
        utils.print_err(
            chat,
            m_traceback.format_exc() if show_traceback else
            f"Command not found: `{func}`. \n"
            f"Prepend `/` or `\\` to ignore command parsing and say this "
            f"message literally, e.g. `/{func}{rest}`"
        )
        return

    args:   List[str]      = []
    kwargs: Dict[str, str] = {}

    for arg in literal_args:
        parts = arg.split("=", maxsplit=1)

        if len(parts) == 1:
            args.append(parts[0])
            continue

        # Used just to normalize shell quotes, escapes, etc
        splitter         = shlex.shlex(" ".join(parts[1:]), posix=True)
        value            = " ".join(list(splitter))
        kwargs[parts[0]] = value

    actual_func(chat, *args, _show_traceback=show_traceback, **kwargs)
