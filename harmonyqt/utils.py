# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import os
from typing import Dict, Optional

from atomicfile import AtomicFile
from PyQt5.QtCore import QStandardPaths as QSP
from PyQt5.QtCore import QDateTime

import requests

from . import data
from .__about__ import __pkg_name__


def get_standard_path(kind:            QSP.StandardLocation,
                      file:            str,
                      initial_content: Optional[str] = None) -> str:
    relative_path = file.replace("/", os.sep)

    path = QSP.locate(kind, relative_path)
    if path:
        return path

    base_dir = QSP.writableLocation(kind)

    if not base_dir.rstrip(os.sep).endswith(f"{os.sep}{__pkg_name__}"):
        base_dir = f"{base_dir}{os.sep}{__pkg_name__}"

    path = f"{base_dir}{os.sep}{relative_path}"
    os.makedirs(os.path.split(path)[0], exist_ok=True)

    if not (initial_content is None or os.path.exists(path)):
        with AtomicFile(path, "w") as new:
            new.write(initial_content)

    return path


def get_config_path(file: str, initial_content: Optional[str] = None) -> str:
    return get_standard_path(QSP.AppConfigLocation, file, initial_content)


def get_error_file(name: str = "") -> str:
    date = QDateTime.currentDateTime().toString("yyyyMMdd-HHmmss")
    file = "errors/session_%s.txt" % "_".join((s for s in (date, name) if s))
    return get_standard_path(QSP.AppDataLocation, file)


def get_ip_info(ip: Optional[str] = None) -> Dict[str, str]:
    try:
        response = requests.get(f"https://ipinfo.io/{ip or ''}", timeout=6.5)
        response.raise_for_status()
    except requests.RequestException:
        return {}

    di = response.json()
    if "country" not in di:
        return di

    di["country"] = data.SHORT_COUNTRY_CODES.get(di["country"], di["country"])
    return di
