# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import threading
from pprint import pprint
from queue import Queue
from typing import Dict

# pylint: disable=no-name-in-module

from .accounts import AccountTuple, LoggedAccountsType


class EventManager:
    def __init__(self, accounts: LoggedAccountsType) -> None:
        self._accounts = accounts
        self._lock     = threading.Lock()


        self.oldest_rooms_event: Dict[str, Dict[str, dict]] = {}
        # self.messages[account.user.user_id[room.room_id[Queue[event]]]
        self.messages:           Dict[str, Dict[str, Queue]] = {}

        for acc in self._accounts.values():
            self.messages[acc.user.user_id]           = {}
            self.oldest_rooms_event[acc.user.user_id] = {}

            acc.client.add_listener(lambda e, a=acc: self.on_event(a, e))
            acc.client.start_listener_thread()


    def on_event(self, account: AccountTuple, event: dict) -> None:
        with self._lock:
            print(account.user.user_id)
            pprint(event)
            print()

            if event["type"] == "m.room.message":
                acc_events    = self.messages[account.user.user_id]
                oldests_event = self.oldest_rooms_event[account.user.user_id]

                if event["room_id"] not in oldests_event:
                    oldests_event[event["room_id"]] = event

                if event["room_id"] not in acc_events:
                    acc_events[event["room_id"]] = Queue()

                acc_events[event["room_id"]].put(event)
