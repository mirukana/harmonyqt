# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import pdb as actual_pdb
import shlex

import docopt
# pylint: disable=no-name-in-module
from PyQt5.QtCore import pyqtRemoveInputHook

from . import REGISTERED_COMMANDS, register, say, utils
from ..chat import Chat


@register(run_in_thread=False)
# pylint: disable=redefined-builtin
def eval(chat: Chat, args: dict) -> None:
    """Usage: /eval TEXTS... [-p|--pdb-parse -P|--pdb-run]

    Evaluate and either `/say` the `TEXTS` or run them as commands.

    Options:
      -p, --pdb-parse
        Enter the Python debugger as soon as possible,
        when the command is being parsed.

      -P, --pdb-run
        Enter the Python debugger when the command or `/say` is about
        to be executed.

    Examples:
    ```
      /eval Hi!
      /eval "Message 1 with spaces" "Message 2"
      /eval "/help --full"
      /eval "/eval '/badcommand test'" -P
    ```"""

    pdb_lvl = 2 if args["--pdb-run"] else 1 if args["--pdb-parse"] else 0

    for text in args["TEXTS"]:
        eval_f(chat, text=text, pdb_level=pdb_lvl)


def eval_f(chat: Chat, text: str, pdb_level: int = 0) -> None:
    if pdb_level == 1:
        pyqtRemoveInputHook()
        actual_pdb.set_trace()  # pylint: disable=no-member

    ignore_cmd = text.startswith("//") or text.startswith(r"\/")

    if text.startswith("///") or text.startswith(r"\\/"):
        text = text[1:]

    if ignore_cmd or not text.startswith("/"):
        say.say_f(chat, text)
        return

    try:
        func, *args = shlex.split(text)
    except ValueError as err:
        utils.print_exception(chat, err)
        return

    try:
        parse_func = REGISTERED_COMMANDS[func.lstrip("/")]
    except KeyError:
        utils.print_err(
            chat,
            f"Command not found: `{func}`. \n"
            f"Type `/help` to see available commands.\n"
            f"Prepend `/` or `\\` to ignore command parsing and say this "
            f"message literally, e.g. `/{func}{' …' if args else ''}`."
        )
        return

    try:
        args = docopt.docopt(parse_func.__doc__, help=False, argv=args)
    except docopt.DocoptExit:
        utils.print_err(
            chat,
            f"Invalid command syntax or bad option, "
            f"see `/help {func.lstrip('/')}`."
        )
    except docopt.DocoptLanguageError as err:
        utils.print_exception(chat, err, parse_func)
    else:
        parse_func(chat, args, _pdb_level=pdb_level)
