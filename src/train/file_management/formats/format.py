from abc import ABC, abstractmethod
from datetime import date, time, timedelta
from typing import TypedDict


class Standard(TypedDict):
    priority: int
    date: date
    block_section_or_yard: str
    corridor_block: str
    line: str
    demanded_time_from: time
    demanded_time_to: time
    block_demanded: timedelta
    permitted_time_from: time | None
    permitted_time_to: time | None
    block_permitted: timedelta | None
    department: str
    den: str
    nature_of_work: str
    location: str


class Format(ABC):
    @staticmethod
    @abstractmethod
    def convert_to_standard(data: dict) -> Standard: ...

    @staticmethod
    @abstractmethod
    def convert_from_standard(standard: Standard) -> dict: ...


class ParseHelper:
    @staticmethod
    def get_time(raw: str) -> time | None:
        try:
            return time.fromisoformat(str(raw).strip())
        except ValueError:
            return None

    @staticmethod
    def get_int(raw: str, default: int = 0) -> int:
        try:
            return int(str(raw).strip())
        except ValueError:
            return default

    @staticmethod
    def get_date(raw: str) -> date | None:
        try:
            return date.fromisoformat(str(raw).strip())
        except ValueError:
            return None
