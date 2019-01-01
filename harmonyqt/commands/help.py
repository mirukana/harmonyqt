# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
from inspect import cleandoc
from typing import List

from . import REGISTERED_COMMANDS, register, utils
from ..chat import Chat


# pylint: disable=redefined-builtin
@register
def help(chat: Chat, args: dict) -> None:
    """Usage: /help [COMMANDS]... [-f|--full]

    Show commands overview, or the full help for COMMANDS.

    Options:
      -f, --full
        Show full help for all commands if no COMMAND is specified.

    Examples:
    ```
      /help
      /help say
      /help say nick
      /help -f
    ```"""

    help_f(chat, commands=args["COMMANDS"], full=bool(args["--full"]))


def help_f(chat: Chat, commands: List[str], full: bool = False) -> None:
    cmd_helps: List[str] = []

    full     = bool(commands) or full
    show_all = not commands
    commands = [c.lstrip("/") for c in commands] or sorted(REGISTERED_COMMANDS)

    for name in commands:
        try:
            func = REGISTERED_COMMANDS[name]
        except KeyError:
            utils.print_err(chat, f"Command not found: `{name}`.")
            continue

        if not func.__doc__:
            utils.print_err(chat, f"Missing help for `{name}`.")
            continue

        try:
            cmd_helps.append(format_doc(cleandoc(str(func.__doc__)), full))
        except Exception as err:
            utils.print_exception(chat, err, func)
            continue

    text = "<pre class=help>%s%s</pre>" % (
        "<span class='title section'>Available commands:</span><br>"
        if show_all else "",

        ("<br><br>" if full else "<br>").join(cmd_helps),
    )
    utils.print_info(chat, text, is_html=True)


class HelpParseError(Exception):
    def __init__(self, docstring: str) -> None:
        super().__init__(
            "Docstring must have an usage, short description and optionally a "
            "body (option details, etc); each separated by a blank line."
        )
        self.docstring = docstring


def format_doc(doc: str, full: bool = False) -> str:
    # Prevent < > chars in doc from being processed as HTML
    doc = doc.replace(">", "&gt;").replace("<", "&lt;")

    doc = re.sub(r"^(?!\s)(.+:)$",  # ^Title:
                 r"<span class='title command-section'>\1</span>",
                 doc,
                 flags=re.MULTILINE)
    doc = re.sub(r"(?:^|(?<=>))```\n((?:.|\n)+)\n```(?=$|<)",  # code fences
                 r"<code>\1</code>",
                 doc,
                 flags=re.MULTILINE)
    doc = re.sub(r"(?:^|(?<=[^`]))`([^`]+)`(?=$|[^`])", # `code`
                 r"<code>\1</code>",
                 doc)
    op  = {"o": r"A-Za-z\d-"}
    doc = re.sub(  # -o, --options
        r"(?:^|(?<=[^%(o)s]))(-[%(o)s]|--[%(o)s]{2,})(?=$|[^%(o)s])" % op,
        r"<code class=option>\1</code>",
        doc
    )
    doc = re.sub(  # -o/--options ARGUMENTS
        r"(<code class=option>.+?</code>\s*)([A-Z\d_]{2,})",
        r"\1<code class=option-arg>\2</code>",
        doc
    )

    try:
        usage, desc, *rest = doc.strip().split("\n\n", maxsplit=2)
    except ValueError:
        raise HelpParseError(doc)

    usage = "<code class='title command'>%s</code>" % re.sub(
        r"^(?:(?:<.+>)*usage:(?:<.+>)*)?\s*",
        "",
        usage,
        flags = re.IGNORECASE | re.MULTILINE
    )

    desc = f"<div class=description>{desc}</div>"
    body = f"<div class=body>{rest[0]}</div>" if rest else ""

    elements = [usage, desc]
    if full and body:
        elements.append(body)

    return "<div class=command-help>%s</div>" % \
           ("<br>" if full else "").join(elements)
