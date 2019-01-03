# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import pdb as actual_pdb
import shlex
from typing import Callable, Dict, Optional

import docopt
from PyQt5.QtCore import pyqtRemoveInputHook

from . import REGISTERED_COMMANDS, register, say, utils
from .. import main_window
from ..chat import Chat, RoomNotJoinedError, UserNotLoggedInError

EVAL_PARSING_HOOKS: Dict[str, Callable[[Chat, str, bool], str]] = {}


@register
# pylint: disable=redefined-builtin
def eval(chat: Chat, args: dict) -> None:
    """Usage: /eval TEXTS... [-u ID|--user ID -p LEVEL|--pdb LEVEL]

    Run `TEXTS` as commands. If a text doesn't start with `/`, `/say` is used.

    Options:
      -u ID, --user ID
        Say/execute `TEXTS` with a different logged-in user account.
        Right click on an account in the Accounts / Rooms pane to copy its ID.

        Multiple users can be specified by separating them with a comma.

        `ID` can also be one of the following:
        - `@`: Will be replaced by your current user;
        - `*`: Will be replaced by all your logged-in users;
        - `&`: Same as above, excluding your current user.

        If you pass an username instead of a proper ID
        (e.g. `alice` instead of `@alice:matrix.org`),
        the server is assumed to be the same as your current user.

      -p LEVEL, --pdb LEVEL
        Enter the Python debugger. `LEVEL` determines where to start:
        - `1`: As soon as possible, when `TEXTS` are about to be parsed;
        - `2`: When `TEXTS` are about to be said/executed.

    Examples:
    ```
      /eval Hi!
      /eval "Message 1 with spaces" "Message 2"
      /eval "/help --full"
      /eval "/eval '/badcommand test'" -p 2

      /eval Hi! -u @my_other_account:matrix.org
      /eval Hi! -u @,account2,account3
      /eval Hi! -u *
    ```"""

    assert args["--pdb"] in (None, "1", "2"), "--pdb must be `1` or `2`."
    pdb_lvl = 0 if not args["--pdb"] else int(args["--pdb"])

    if pdb_lvl == 1:
        pyqtRemoveInputHook()
        actual_pdb.set_trace()  # pylint: disable=no-member

    users = [chat.client.user_id]

    if args["--user"]:
        users      = args["--user"].split(",")
        current    = chat.client.user_id
        all_logged = [uid for uid, client in main_window().accounts.items()
                      if chat.room.room_id in client.rooms]

        all_logged_no_current = [u for u in all_logged if u != current]

        users = [current if u == "@" else u for u in users]

        while "*" in users:
            index = users.index("*")
            users = users[:index] + all_logged + users[index + 1:]

        while "&" in users:
            index = users.index("&")
            users = users[:index] + all_logged_no_current + users[index + 1:]

    for user in users:
        for text in args["TEXTS"]:
            eval_f(chat, text=text, user_id=user, pdb_level=pdb_lvl)


def eval_f(chat:      Chat,
           text:      str,
           user_id:   Optional[str] = None,
           pdb_level: int           = 0) -> None:

    if user_id:
        if user_id.startswith("@") and ":" not in user_id:
            user_id = user_id[1:]

        if not user_id.startswith("@"):
            server  = chat.client.user_id.split(":")[-1]
            user_id = f"@{user_id}:{server}"

        try:
            chat = Chat(user_id, chat.room.room_id)
        except (UserNotLoggedInError, RoomNotJoinedError) as err:
            utils.print_err(chat, str(err))
            return

    force_say = False
    if text.startswith("//") or text.startswith(r"\/"):
        force_say = True
        text      = text[1:]

    for hook in EVAL_PARSING_HOOKS.values():
        text = hook(chat, text, force_say)
        if not text:
            return

    if force_say or not text.startswith("/"):
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
