# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
from inspect import Parameter, cleandoc, signature
from typing import List

from . import REGISTERED_COMMANDS, register, utils
from ..chat import Chat


# pylint: disable=redefined-builtin
@register
def help(chat: Chat, commands: str = "", full: str = "no") -> None:
    """Show commands overview, or the full help of specified `commands`.
    The full help for all commands can be requested with `full=yes`.

    Examples:

        /help
        /help full=yes
        /help say
        /help say,nick
    """
    cmd_helps: List[str] = []

    want_cmds = utils.str_arg_to_list(commands)
    show_full = True if want_cmds else utils.str_arg_to_bool(full)

    for cmd in want_cmds:
        if cmd not in REGISTERED_COMMANDS:
            utils.print_err(chat, f"Command not found: `{cmd}`")
            return

    for name, func in sorted(REGISTERED_COMMANDS.items()):
        if want_cmds and name not in want_cmds:
            continue

        args: List[str] = []

        for aname, arg in list(signature(func).parameters.items())[1:]:
            has_default   = arg.default is not Parameter.empty
            default       = str(arg.default) if has_default else ""
            quote_default = not default.strip() or re.findall(r"\s", default)
            is_var_pos    = arg.kind == Parameter.VAR_POSITIONAL
            is_var_kw     = arg.kind == Parameter.VAR_KEYWORD

            args.append("".join((
                "["   if has_default or is_var_pos or is_var_kw else "",
                "key" if is_var_kw                              else aname,

                ("={0}{1}{0}".format('"' if quote_default else '', default)
                 if has_default and default and default != "@" else ""),

                "=value" if is_var_kw                              else "",
                "]"      if has_default or is_var_pos or is_var_kw else "",
                "..."    if is_var_pos or is_var_kw                else "",
            )))

        desc = cleandoc(func.__doc__ or "").strip()
        if not show_full and desc:
            desc = desc.splitlines()[0]

        cmd_helps.append(f"## `/{name} {' '.join(args)}`\n{desc}")

    text = "\n".join((
        "# Available commands" if not want_cmds else "",
        "\n\n".join(cmd_helps),
    ))
    print(text)
    utils.print_info(chat, text)
