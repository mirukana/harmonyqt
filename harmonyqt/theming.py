# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import abc
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from pkg_resources import resource_filename
from PyQt5.QtGui import QIcon

from . import __about__

_PKG = __about__.__name__


class ResourceDir(abc.ABC):
    def __init__(self, base_dir: str, res_name: str) -> None:
        self.name:      str  = res_name
        self.dir:       str  = f"{base_dir}/{res_name}"
        self.base_path: Path = Path(resource_filename(_PKG, self.dir))

        # {relative path: {ext: (path, file content as bytes)}}
        self._cache: Dict[str, Dict[str, Tuple[Path, Any]]] = {}
        self.reload()


    def reload(self) -> None:
        self._cache_dir(self.base_path)


    def _cache_dir(self, path: Path) -> None:
        for item in path.iterdir():
            if item.is_dir():
                self._cache_dir(item)
            if item.is_file():
                self._cache_file(item)


    def _cache_file(self, path: Path) -> None:
        key, ext = "/".join(path.relative_to(self.base_path).parts)\
                   .split(".", maxsplit=1)

        file_dict      = self._cache.setdefault(key, {})
        file_dict[ext] = (path, self.cache_file_content(path))


    @abc.abstractmethod
    def cache_file_content(self, path: Path) -> Any:
        pass


    def get_resource(self, relative_path: str, exts: Sequence[str]
                    ) -> Tuple[Path, Any]:
        not_found: List[Path] = []

        for ext in exts:
            try:
                return self._cache[relative_path][ext]
            except KeyError:
                not_found.append(self.base_path / f"{relative_path}.{ext}")

        obj   = type(self).__name__.lower()
        files = "\n".join((f"  {p!s}" for p in not_found))
        raise FileNotFoundError(
            f"None of these files found for {obj} {self.name!r}:\n{files}"
        )


class Theme(ResourceDir):
    def __init__(self, name: str) -> None:
        super().__init__("themes", name)


    def cache_file_content(self, path: Path) -> str:
        return path.read_text()


    def style(self, relative_path: str) -> str:
        return self.get_resource(relative_path, ("qss", "css"))[1]


class Icons(ResourceDir):
    def __init__(self, name: str) -> None:
        super().__init__("icons", name)


    def cache_file_content(self, path: Path) -> QIcon:
        return QIcon(str(path))


    def path(self, relative_path: str) -> str:
        return str(self.get_resource(relative_path, ("png",))[0])


    def icon(self, relative_path: str) -> str:
        return self.get_resource(relative_path, ("png",))[1]
