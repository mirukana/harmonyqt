# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import base64
import json
import os
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from atomicfile import AtomicFile
from dataclasses import dataclass, field
from PyQt5.QtCore import QDateTime, QStandardPaths

from . import main_window


@dataclass
class EventLogger:
    base_dir:                Optional[os.PathLike] = None
    filename_format:         str                   = "{room_id}/{date}.json"
    date_format:             str                   = "yyyy-MM-dd"
    base32_room_id:          bool                  = True
    allow_event_overwriting: bool                  = True

    json_dumps_kwargs: Dict[str, Any] = field(default_factory=dict)

    _pool: ThreadPool = field(init=False, repr=False, default=ThreadPool(1))


    def __post_init__(self) -> None:
        qsp = QStandardPaths
        self.base_dir = (
            Path(self.base_dir) if self.base_dir else
            Path(qsp.writableLocation(qsp.AppDataLocation)) / "logs"
        )
        self.json_dumps_kwargs = self.json_dumps_kwargs or {
            "indent":       4,
            "ensure_ascii": False,
            "sort_keys":    True,
        }
        self._pool = ThreadPool(1)


    def start(self, autolog_funcs: Sequence[Callable[[dict], None]] = (),
             ) -> None:
        for func in autolog_funcs or (self.log_to_file,):
            main_window().events.signal.new_unique_event.connect(
                lambda _, ev, f=func: self._pool.apply_async(
                    f, (ev,), error_callback=self.on_log_error,
                )
            )


    @staticmethod
    def on_log_error(err: BaseException) -> None:
        raise err


    def log_to_file(self, event: dict) -> None:
        path = self.base_dir / self.filename_format.format(  # type: ignore
            room_id = self.encode_room_id(event["room_id"]),
            date    = QDateTime.fromMSecsSinceEpoch(event["origin_server_ts"])\
                      .toString(self.date_format)
        )

        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]")

        with open(path, "r") as in_file, AtomicFile(path, "w") as out_file:
            logged: List[dict] = json.loads(in_file.read())

            if self.allow_event_overwriting:
                logged = [e for e in logged
                          if e["event_id"] != event["event_id"]]
            else:
                for logged_ev in logged:
                    if logged_ev["event_id"] == event["event_id"]:
                        return

            logged.append(event)
            logged.sort(key=lambda ev: ev["origin_server_ts"])

            out_file.write(json.dumps(logged, **self.json_dumps_kwargs))


    def encode_room_id(self, room_id: str) -> str:
        return (
            base64.b32encode(bytes(room_id, "utf-8")).decode("utf-8").lower()
            if self.base32_room_id else room_id
        )


    def decode_room_id(self, encoded: str) -> str:
        return (
            base64.b32decode(bytes(encoded, "utf-8"), casefold=True)
            .decode("utf-8")

            if self.base32_room_id else encoded
        )
