from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from train.file_management import FileManager
    from train.models.task import PartialTask


class UnsupportedFileTypeError(Exception):
    def __init__(self, ext: str) -> None:
        super().__init__(f"Unknown file extension `{ext}`")


class InvalidFileDataError(Exception):
    pass


class CriticalLogicError(Exception):
    pass


class NoFreeWindowError(Exception):
    def __init__(self, taskq: PartialTask) -> None:
        super().__init__(f"No window could fit the task `{taskq}`")


class InvalidHeadersError(Exception):
    def __init__(self, fmt: FileManager.Format, headers: list[str]) -> None:
        super().__init__(f"Invalid headers `{headers}` for format `{fmt}`")
