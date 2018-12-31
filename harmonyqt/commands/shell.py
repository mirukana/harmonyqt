# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re
import subprocess as sp
from typing import Optional, Union

from . import register, say, utils
from ..chat import Chat


@register
def shell(chat: Chat, args: dict) -> None:
    """
    Usage:
      /shell COMMAND [-e|--echo -c|--no-cmd -b|--no-block -s PATH|--shell PATH]

    Run a `COMMAND` with the OS shell, send standard output.

    When the command finishes,
    - Its return code will be shown if it isn't `0`
    - stderr will be shown if it contains anything
    - stdout will be shown/sent if the command outputted anything.

    ANSI escape codes are stripped from outputs.

    Options:
      -e, --echo
        Print standard output locally without sending it.

      -c, --no-cmd
        Do not print the command used before output.

      -b, --no-block
        Do not format the output as a monospace font code block.

      -s PATH, --shell PATH
        Path of the shell to run the command with.
        The default on POSIX systems (GNU/Linux, OSX, …) is `/bin/sh`,
        which may be a symbolic link to `/bin/bash` on some distributions.

    Examples (POSIX):
    ```
        /shell uptime
        /shell date --no-cmd --no-block
        /shell 'echo "It is $(date '+%T') here"' -cb
        /shell "ls -l ~"
        /shell "echo $SHELL" -s /bin/bash
        /shell "neofetch || screenfetch && echo 'It works!'"
    ```"""

    shell_f(
        chat          = chat,
        command       = args["COMMAND"],
        echo          = args["--echo"],
        no_command    = args["--no-cmd"],
        no_code_block = args["--no-block"],
        shell_path    = args["--shell"],
    )


def shell_f(chat:          Chat,
            command:       str,
            echo:          bool          = False,
            no_command:    bool          = False,
            no_code_block: bool          = False,
            shell_path:    Optional[str] = None) -> None:

    process = sp.Popen(
        command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE,
        executable=shell_path or None
    )
    stdout, stderr = process.communicate()
    retcode        = process.returncode

    command = _treat_output(command)
    stdout  = _treat_output(stdout)
    stderr  = _treat_output(stderr)

    if retcode and retcode != 0:
        utils.print_warn(chat, f"`{command}` returned `{retcode}`.")

    if stderr:
        utils.print_warn(chat, f"```\n{stderr}\n```")

    if stdout:
        bticks = ("", "") if no_code_block else ("```\n", "\n```")
        text   = "\n".join((
            bticks[0] if no_command else f"{bticks[0]}$ {command}",
            f"{stdout}{bticks[1]}"
        ))

        if echo:
            utils.print_info(chat, text)
        else:
            say.say_f(chat, text)


def _treat_output(text: Union[bytes, str]) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # Strip ANSI escape sequences:
    text = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)

    # zero-width space to "escape" triple-backticks and prevent glitching
    # the code block/command without altering what the user sees or can select:
    text = text.replace("```", "\u200b```")

    # Strip whitespace at the end
    return text.rstrip()
