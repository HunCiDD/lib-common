from __future__ import annotations

__all__ = [
    "Dir",
    "EnvFile",
    "File",
    "FileException",
    "IniFile",
    "JsonFile",
    "XmlFile",
    "YamlFile",
]

import json
import os
import shutil
import stat
from collections.abc import Callable
from configparser import ConfigParser
from functools import reduce
from pathlib import Path
from typing import Any

from defusedxml import ElementTree
from dotenv import dotenv_values
from yaml import safe_load

from lib_common.data.utils.encoder import JsonEncoder

MODES = stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
FLAGS = {
    "r": os.O_RDONLY,
    "rb": os.O_RDONLY,
    "w": os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
    "wb": os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
    "w+": os.O_RDWR | os.O_CREAT | os.O_TRUNC,
    "a": os.O_WRONLY | os.O_CREAT | os.O_APPEND,
    "ab": os.O_WRONLY | os.O_CREAT | os.O_APPEND,
    "a+": os.O_RDWR | os.O_CREAT | os.O_APPEND,
    "ab+": os.O_RDWR | os.O_CREAT | os.O_APPEND,
}


class FileException(Exception): ...


class Base:
    ALLOWED_SUFFIX = ()

    def __init__(self, path: str | Path):
        self._path = path if isinstance(path, Path) else Path(path)
        # 换成绝对路径
        self._path = self._path.resolve()
        self.name = self._path.name
        self.suffix = self._path.suffix

        if self.ALLOWED_SUFFIX and self.suffix not in self.ALLOWED_SUFFIX:
            raise FileException(f"Invalid suffix: {self.suffix}")

    def __str__(self) -> str:
        return str(self._path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def exist(self) -> bool:
        return self._path.exists()

    @property
    def stat(self) -> os.stat_result:
        return self._path.stat()

    @property
    def size(self) -> int:
        if self.exist:
            return self.stat.st_size
        return 0

    @property
    def mtime(self):
        if self.exist:
            return self.stat.st_mtime
        return 0

    def remove(self):
        os.remove(self._path)


class File(Base):
    def open(self, mode: str = "r", encoding="utf-8"):
        """安全方式打开文件
        :param mode:
        :param encoding:
        :return:
        """
        if mode not in FLAGS:
            raise FileException(f"Invalid mode: {mode}")
        if "b" in mode:
            fp = os.fdopen(os.open(self._path, FLAGS[mode], MODES), mode)
        else:
            fp = os.fdopen(os.open(self._path, FLAGS[mode], MODES), mode, encoding=encoding)
        return fp

    def read(self, mode: str = "r", encoding="utf-8", size: int = -1) -> str:
        with self.open(mode, encoding) as fp:
            return fp.read(size)

    def write(self, data: Any, mode: str = "w", encoding="utf-8", size: int = -1):
        with self.open(mode, encoding) as fp:
            if size > 0:
                fp.truncate(size)
            fp.write(data)

    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        raise FileException("Load not support")

    def dump(self, data: dict[str, Any], encoding: str = "utf-8"): ...


class Dir(Base):
    @property
    def size(self) -> int:
        if self.exist:
            return reduce(lambda x, y: x + y, [f.size for f in self.files()], 0)
        return 0

    @property
    def empty(self) -> bool:
        return not any(self._path.iterdir())

    @property
    def count(self) -> int:
        return len(self.iters())

    def iters_level(self, cur_level: int = 0, max_level: int = -1) -> list[Dir | File]:
        items = []
        for _path in self._path.iterdir():
            if cur_level > max_level >= 0:
                break

            if cur_level > 9:
                break

            if _path.is_dir():
                _dir = Dir(_path)
                items.append(_dir)
                items.extend(_dir.iters_level(cur_level + 1, max_level))
            else:
                _file = File(_path)
                items.append(_file)
        return items

    def iters(self, max_level: int = -1) -> list[Dir | File]:
        return self.iters_level(0, max_level)

    def files(self, max_level: int = -1) -> list[File]:
        return [item for item in self.iters(max_level) if isinstance(item, File)]

    def dirs(self, max_level: int = -1) -> list[Dir]:
        return [item for item in self.iters(max_level) if isinstance(item, Dir)]

    def remove(self):
        shutil.rmtree(self._path)

    def is_relative(self, _path: Dir | File | str | Path) -> bool:
        """判断当前目录是否包含某个路径
        :param _path:
        :return:
        """
        if isinstance(_path, Dir | File):
            path = _path.path
        elif isinstance(_path, Path):
            path = _path
        else:
            path = Path(_path)
        return path.is_relative_to(self._path)

    def relative_to(self, _path: Dir | File | str | Path) -> Path:
        """获取当前目录相对于某个路径的相对路径"""
        if isinstance(_path, Dir | File):
            path = _path.path
        elif isinstance(_path, Path):
            path = _path
        else:
            path = Path(_path)
        return path.relative_to(self._path)

    def relative_root_dir(self, _path: Dir | File | str | Path) -> str:
        re_path = self.relative_to(_path)
        return re_path.parts[0]


class JsonFile(File):
    ALLOWED_SUFFIX = (".json",)

    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        data = {}
        with self.open("r", encoding=encoding) as fp:
            data.update(json.load(fp))

            if hook:
                data = hook(data)
        return data

    def dump(self, data: dict[str, Any], encoding: str = "utf-8"):
        with self.open("w", encoding=encoding) as fp:
            json.dump(data, fp, indent=4, cls=JsonEncoder)


class EnvFile(File):
    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        data = {**dotenv_values(dotenv_path=self._path, encoding=encoding)}
        return data

    def dump(self, data: dict[str, Any], encoding: str = "utf-8"):
        raise FileException("Dump not support")


class IniFile(File):
    ALLOWED_SUFFIX = (".ini", ".conf", ".env")

    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        data = {}
        parser = ConfigParser()
        parser.read(self._path, encoding=encoding)
        for section in parser.sections():
            section_data = {}
            for key, value in parser.items(section):
                section_data[key] = value
            data[section] = section_data

        if hook:
            data = hook(data)
        return data

    def dump(self, data: dict[str, Any], encoding: str = "utf-8"):
        raise FileException("Dump not support")


class XmlFile(File):
    ALLOWED_SUFFIX = (".xml",)

    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        _parser = ElementTree.XMLParser(encoding=encoding, forbid_dtd=True, forbid_entities=True)
        data = {}
        with self.open("r", encoding=encoding) as fp:
            tree = ElementTree.parse(fp, parser=_parser)
            if hook:
                data = hook(data, tree)
        return data


class YamlFile(File):
    ALLOWED_SUFFIX = (".yaml", ".yml")

    def load(self, encoding: str = "utf-8", hook: Callable | None = None) -> dict[str, Any]:
        data = {}
        with self.open("r", encoding=encoding) as fp:
            data.update(safe_load(fp))

            if hook:
                data = hook(data)
        return data
