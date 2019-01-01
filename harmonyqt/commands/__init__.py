# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

r''' OUDATED
Registered functions represent commands.
A command will be started in its own thread to not block the client, unless
`@register_command(run_in_thread=False)` is used.

Functions will receive a `harmonyqt.chat.Chat` object as first argument,
representing the chat from which the user typed the command.
Other arguments will be strings corresponding to what the user typed after
the `/function_name `.

Unless the wanted type for an argument *is* `str`, it must be manually
converted to its appropriate types.  Common types:
- Integer number (convert with `int(arg)`)
- Decimal number (`float(arg)`)
- Boolean (use `str_arg_to_bool(arg)` from harmonyqt.commands.utils)
- List of integer, decimal, string or boolean values
  (use `str_arg_to_list` from harmonyqt.commands.utils).

When taking user ID arguments, use `expand_user(user)` from
`harmonyqt.commands.utils` for each ID.
This provides features like expanding a single `@` to the ID of the user that
typed the command.

A function should have a docstring. The first line will be shown in `/help`,
and the full docstring will be shown with `/help <function name>`.
The docstring can include markdown formatting, except images.

This example command:
```python3
    from harmonyqt.chat import Chat
    from harmonyqt.commands.utils import str_arg_to_list

    @register
    def nudge(chat: Chat, users: str, times: str = "1") -> None:
        """Send an alert to users X times."""
        users_list = [expand_user(u) for u in str_arg_to_list(users)]
        times_int  = int(times)
        ...
```

May be used in the following ways from a chat:

    /nudge @alice:matrix.org
    /nudge @alice:matrix.org,@marisa:matrix.org 3
    /nudge @alice:matrix.org,"value,with,comma or space" times=1
    /nudge times="1" users=@alice:matrix.org,"value,with,comma or space"
    ...

Any value containing spaces (and commas (`,`) for list values) must be put
inside quotes, or the bad character must be escaped using a
backslash (`\`) before it.'''

import functools
import shlex
import pdb as actual_pdb
import traceback
from threading import Thread
from typing import Callable, Dict, List, Optional, Union

from PyQt5.QtCore import pyqtRemoveInputHook

from . import utils
from ..chat import Chat

FuncType = Callable[..., None]

REGISTERED_COMMANDS: Dict[str, FuncType] = {}


def register(func: Optional[FuncType] = None, run_in_thread: bool = True):
    # func will be None if called without parentheses.

    def decorator(func: FuncType):
        def executor(*args, _pdb_level: int = 0, **kwargs) -> None:
            try:
                if _pdb_level == 2:
                    pyqtRemoveInputHook()
                    actual_pdb.set_trace()  # pylint: disable=no-member

                func(*args, **kwargs)
            except Exception as err:
                utils.print_exception(chat=args[0], err=err, bad_func=func)

        @functools.wraps(func)
        def wrapper(chat: Chat, *args, _pdb_level: int = 0,  **kwargs) -> None:
            args_ = [chat] + list(args)

            if _pdb_level > 0 or not run_in_thread:
                executor(*args_, _pdb_level=_pdb_level, **kwargs)
            else:
                Thread(target=executor, args=args_, kwargs=kwargs, daemon=True
                      ).start()

        REGISTERED_COMMANDS[func.__name__] = wrapper
        return wrapper

    # Allow decorator to be called with or without parentheses:
    if callable(func):
        return decorator(func)
    return decorator


# pylint: disable=wrong-import-position,redefined-builtin,reimported
# Standard core commands, cannot be disabled
from . import eval, say, help
# Other commands
from . import alias, autorun, nick, pdb, shell, room_set
