# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import os
from typing import Optional

from atomicfile import AtomicFile
from PyQt5.QtCore import QStandardPaths as QSP


def get_standard_path(kind:            QSP.StandardLocation,
                      file:            str,
                      initial_content: Optional[str] = None) -> str:
    relative_path = file.replace("/", os.sep)

    path = QSP.locate(kind, relative_path)
    if path:
        return path

    base_dir = QSP.writableLocation(kind)
    path     = f"{base_dir}{os.sep}{relative_path}"
    os.makedirs(os.path.split(path)[0], exist_ok=True)

    if initial_content is not None:
        with AtomicFile(path, "w") as new:
            new.write(initial_content)

    return path


def get_config_path(file: str, initial_content: Optional[str] = None) -> str:
    return get_standard_path(QSP.AppConfigLocation, file, initial_content)
