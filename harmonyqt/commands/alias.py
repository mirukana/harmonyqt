# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import shlex
from typing import List

from dataclasses import dataclass

from . import eval as m_eval
from . import register
from ..chat import Chat


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


    def expand(self, _: Chat, typed_text: str) -> str:
        if self.is_global_words:
            return typed_text.replace(self.alias, self.expands_to)

        if self.is_global:
            return re.sub(rf"(?:^|(?<=\s))({self.alias})(?=$|\s)",
                          self.expands_to.replace("\\", "\\\\"),
                          typed_text)

        args: List[str] = shlex.split(typed_text)

        if args[0] != self.alias:
            return typed_text

        text = self.expands_to
        text = text if "{}" in text else "%s {}" % text

        if self.single_arg:
            return text.format(shlex.quote(" ".join(args[1:])))

        return text.format(" ".join((shlex.quote(a) for a in args[1:])))


    def register(self) -> None:
        m_eval.EVAL_PARSING_HOOKS[f"alias: {self.alias}"] = self.expand


@register
def alias(_: Chat, args: dict) -> None:
    r"""
    Usage:
      /alias ALIAS EXPANDS_TO [-s|--single-arg|-g|--global|-G|--global-words]

    Define a shortcut for a command.

    For example, doing `/alias /h /help` will let you use `/h` as a command,
    just as if you typed `/help`.

    Note that aliases defined with this command only persist until Harmony
    is closed. To keep aliases across restarts, see `/help /autorun`.

    `ALIAS` doesn't have to start with a `/`.

    When using the created alias, arguments after it are appended as-is to
    `EXPANDS_TO`, unless `EXPANDS_TO` contains a `{}` placeholder.
    In that case, the `{}` will be replaced by the arguments.
    To have a literal `{}` in `EXPANDS_TO`, use `{{}}` instead.

    Options:
      -s, --single-arg
        Everything passed after the alias will be treated as a single argument,
        and no quoting is needed.

      -g, --global
        Allow the alias to be used anywhere in the middle of a message.
        Otherwise, the alias only works at the beginning, like normal commands.
        Global aliases do not take arguments.

      -G, --global-words
        Like --global, but also allows usage in the middle of words.

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
    Alias(alias           = args["ALIAS"],
          expands_to      = args["EXPANDS_TO"],
          single_arg      = args["--single-arg"],
          is_global       = args["--global"],
          is_global_words = args["--global-words"]).register()
