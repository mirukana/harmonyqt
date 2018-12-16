# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import abc
import os
from functools import lru_cache

from pkg_resources import resource_filename
# pylint: disable=no-name-in-module
from PyQt5.QtGui import QIcon

from . import __about__
from .__about__ import __doc__

_PKG = __about__.__name__


class Resource(abc.ABC):
    def __init__(self, base_dir: str, res_name: str) -> None:
        self.name:      str       = res_name
        self.dir:       str       = f"{base_dir}/{res_name}"
        self.base_path: str       = resource_filename(_PKG, self.dir)


    def get_resource_path(self, filename: str, exts: tuple,
                          relative: bool = False) -> str:
        not_found = []

        for ext in exts:
            rel_path = f"{self.dir}/{filename}.{ext}"
            path     = resource_filename(_PKG, rel_path)
            if os.path.exists(path):
                return rel_path if relative else path

            not_found.append(path)

        obj   = type(self).__name__.lower()
        files = "\n".join((f"  {f}" for f in not_found))
        raise FileNotFoundError(
            f"None of these files found for {obj} {self.name!r}:\n{files}"
        )


    @lru_cache(128)
    def get_resource_content(self, filename: str, exts: tuple) -> str:
        with open(self.get_resource_path(filename, exts), "r") as file:
            return file.read()


class Theme(Resource):
    def __init__(self, name: str) -> None:
        super().__init__("themes", name)


    def style(self, filename: str) -> str:
        return self.get_resource_content(filename, ("qss", "css"))


class Icons(Resource):
    def __init__(self, name: str) -> None:
        super().__init__("icons", name)


    def path(self, filename: str, relative: bool = False) -> str:
        return self.get_resource_path(filename, ("png",), relative)


    @lru_cache(128)
    def icon(self, filename: str) -> QIcon:
        return QIcon(self.path(filename))
