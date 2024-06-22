from typing import Any
from train.models.task import PartialTask

class UnsupportedFileTypeError(Exception):
    def __init__(self, ext: str) -> None:
        super().__init__(f"Unknown file extension `{ext}`")

class UnknownFileFormatError(Exception):
    def __init__(self, fmt: Any) -> None:
        super().__init__(f"Unknown file format `{fmt}`")

class InvalidFileDataError(Exception): pass

class CriticalLogicError(Exception): pass

class NoFreeWindowError(Exception):
    def __init__(self, taskq: PartialTask) -> None:
        super().__init__(f"No window could fit the task `{taskq}`")