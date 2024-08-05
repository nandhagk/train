from abc import ABC, abstractmethod
from pathlib import Path


class Handler(ABC):
    @staticmethod
    @abstractmethod
    def read_dict(file: Path) -> tuple[list[str], list[dict]]: ...

    @staticmethod
    @abstractmethod
    def write_dict(file: Path, headers: list[str], data: list[dict]) -> None: ...
