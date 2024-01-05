"""
Plugin support.

A plugin is a repository which has a tasks.py
"""
from dataclasses import dataclass

# from importlib import import_module
from pathlib import Path
from typing import Any, Optional


@dataclass
class Plugin:
    name: str
    repo: str
    module: str

    def __post_init__(self):
        raise NotImplementedError("Plugin system is WIP")

    @classmethod
    def from_folder(cls, path: Path) -> Optional["Plugin"]:
        if not path.is_dir():
            return None

    @classmethod
    def from_repository(cls):
        ...

    @classmethod
    def from_module(cls, module: Any) -> Optional["Plugin"]:
        return module
