# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import shlex
from typing import Dict

from dataclasses import dataclass

from . import eval as m_eval
from . import register, utils
from ..chat import Chat

REGISTERED_ALIASES: Dict[str, "Alias"] = {}


@dataclass
class Alias:
    alias:           str  = ""
    expands_to:      str  = ""
    single_arg:      bool = False
    is_global:       bool = False
    is_global_words: bool = False


    def __post_init__(self) -> None:
        assert self.alias and self.expands_to
        assert sum((self.single_arg, self.is_global, self.is_global_words)) < 2


    def expand(self, _: Chat, typed_text: str, force_say: bool = False) -> str:
        re_alias = re.escape(self.alias)
        re_ex    = self.expands_to.replace("\\", "\\\\")

        if self.is_global_words:
            text = re.sub(rf"(^|[^\\])({re_alias})", rf"\1{re_ex}", typed_text)
            return re.sub(rf"\\({re_alias})",        r"\1",         text)

        if self.is_global:
            text = re.sub(rf"(?:^|(?<=\s))({re_alias})(?=$|\s)",
                          re_ex, typed_text)
            return re.sub(rf"(?:^|(?<=\s))\\({re_alias})(?=$|\s)",
                          rf"\1", text)

        if force_say:
            return typed_text

        first_word, *rest = re.split(r"\s", typed_text, maxsplit=1)

        if first_word != self.alias:
            return typed_text

        if rest == []:
            return self.expands_to

        text = self.expands_to
        text = text if "{}" in text else "%s {}" % text

        if self.single_arg:
            return text.format(shlex.quote(rest[0]))

        return text.format(rest[0])


    def register(self) -> None:
        REGISTERED_ALIASES[self.alias]                    = self
        m_eval.EVAL_PARSING_HOOKS[f"alias: {self.alias}"] = self.expand

    def unregister(self) -> None:
        del REGISTERED_ALIASES[self.alias]
        del m_eval.EVAL_PARSING_HOOKS[f"alias: {self.alias}"]


@register
def alias(chat: Chat, args: dict) -> None:
    r"""
    Usage:
      /alias ALIAS
      /alias ALIAS COMMAND [-s|--single-arg|-g|--global|-G|--global-words]
      /alias ALIAS --remove

    Inspect, define or remove a shortcut for a command.

    If `COMMAND` is not specified and `ALIAS` is already defined,
    the `COMMAND` it expands to will be shown, unless `--remove` is used.

    For example, doing `/alias /h /help` will let you use `/h` as a command,
    just as if you typed `/help`.

    Note that aliases defined with this command only persist until Harmony
    is closed. To keep aliases across restarts, see `/help /autorun`.

    `ALIAS` doesn't have to start with a `/`.

    When using the created alias, arguments after it are appended as-is to
    `COMMAND`, unless `COMMAND` contains a `{}` placeholder.
    In that case, the `{}` will be replaced by the arguments.
    To have a literal `{}` in `COMMAND`, use `{{}}` instead.

    Options:
      -s, --single-arg
        Everything passed after the alias will be treated as a single argument,
        and no quoting is needed.

      -g, --global
        Allow the alias to be used anywhere in the middle of a message.
        Otherwise, the alias only works at the beginning, like normal commands.
        Global aliases do not take arguments.
        They can be escaped with a `\`, e.g. if you have a `b` global alias
        and want to say `a b c` literally, write `a \b c` instead.

      -G, --global-words
        Like --global, but also allows usage in the middle of words.

      --remove
        Remove `ALIAS` if it is defined.

    Examples:
    ```
      /alias /echo "/say --echo"
        /echo test
          Print "test" without sending it as a message

        /echo "Lorem ipsum" "sit dolor amet"
          Print "Lorem ipsum" without sending it as a message, then
          print "sit dolor amet".
          Without --single-arg, they are seen as two separate arguments.

      /alias $ "```
      $ {}
      ```"
        $ ls /tmp | wc -l
          Send the text above in a formatted markdown code block.

      /alias --single-arg /sh /shell
        /sh date
          Send the output of your OS's date command.

        /sh --echo "dir ."
          See the list of files in the current OS directory.

      /alias -s @ "/eval --user @my_other_account:matrix.org"
        @ A test message
          Say "A test message" in the chat as @my_other_account:matrix.org

        @ /nick Alice
          Change @my_other_account:matrix.org's display name to Alice

      /alias --global -> →
        Press the -> key
          Say "Press the → key" in the chat, -> is transformed to →
    ```"""

    arglias = args["ALIAS"]

    if not args["COMMAND"]:
        got = REGISTERED_ALIASES.get(arglias)

        if not got:
            utils.print_err(chat, f"No `{arglias}` alias defined.")
        elif args["--remove"]:
            got.unregister()
        else:
            utils.print_info(chat, f"`{arglias}`: `{got.expands_to}`")

        return

    Alias(alias           = arglias,
          expands_to      = args["COMMAND"],
          single_arg      = args["--single-arg"],
          is_global       = args["--global"],
          is_global_words = args["--global-words"]).register()
