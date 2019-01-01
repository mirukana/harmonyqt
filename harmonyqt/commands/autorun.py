# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import json
import os
from typing import List

from atomicfile import AtomicFile

from . import register, utils
from ..chat import CHAT_INIT_HOOKS, Chat
from ..utils import get_config_path
from .eval import eval_f


DEFAULT_CONFIG = """[
    "/alias /h /help",
    "/alias /echo '/say --echo'"
]"""


@register
def autorun(chat: Chat, args: dict) -> None:
    r"""Usage: /autorun [COMMANDS]... [-r|--reload | --reset]

    Add commands to automatically run when Harmony starts.

    If no `COMMANDS` is passed, the `autorun.json` file path will be printed.
    Commands can be manually added, edited or removed in this file.

    Options:
      -r, --reload
        Reload `autorun.json` and execute its commands.
        Note that if you remove a command that had a durable effect like
        `/alias`, the effect will persist until Harmony is restarted.

      --reset
        Reset `autorun.json` back to default and reload. Cannot be undone!

    Examples:
    ```
      /autorun -r
      /autorun "/alias /h /help"
    ```"""

    if args["--reset"]:
        reset_autorun_json(chat)
    elif args["--reload"]:
        load_autorun_json(chat)

    if not args["COMMANDS"]:
        utils.print_info(chat, get_autorun_json_path())
        return

    for cmd in args["COMMANDS"]:
        add_command(chat, cmd)


def get_autorun_json_path() -> str:
    return get_config_path("autorun.json", DEFAULT_CONFIG)


def load_autorun_json(chat: Chat) -> None:
    with open(get_autorun_json_path(), "r") as in_file:
        config: List[str] = json.loads(in_file.read())

    assert isinstance(config, list), \
           "Content of `autorun.json` must be a JSON list of strings."

    for cmd in config:
        eval_f(chat, cmd)


def add_command(chat, command: str) -> None:
    path = get_autorun_json_path()

    with open(path, "r") as in_file, AtomicFile(path, "w") as out_file:
        config: List[str] = json.loads(in_file.read())
        config.append(command)
        out_file.write(json.dumps(config, indent=4, ensure_ascii=False))

    load_autorun_json(chat)


def reset_autorun_json(chat) -> None:
    path = get_autorun_json_path()
    if os.path.exists(path):
        os.remove(path)

    load_autorun_json(chat)


CHAT_INIT_HOOKS["load_autorun_json"] = load_autorun_json
