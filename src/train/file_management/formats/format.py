from abc import ABC, abstractmethod
from typing import TypedDict
from datetime import date, datetime, time, timedelta

from train.db import decode_datetime, decode_time

class Standard(TypedDict):
    priority             : int
    date                 : date
    block_section_or_yard: str
    corridor_block       : str
    line                 : str
    demanded_time_from   : time
    demanded_time_to     : time
    block_demanded       : timedelta
    permitted_time_from  : time | None
    permitted_time_to    : time | None
    block_permitted      : timedelta | None
    department           : str
    den                  : str
    nature_of_work       : str
    location             : str


class Format(ABC):
    @staticmethod
    @abstractmethod
    def convert_to_standard(data: dict) -> Standard:
        ...

    @staticmethod
    @abstractmethod
    def convert_from_standard(standard: Standard) -> dict:
        ...


class ParseHelper:
    @staticmethod
    def get_time(raw: str) -> time | None:
        try:
            return decode_time(str(raw).strip())
        except ValueError as e:

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
            return decode_datetime(str(raw).strip()).date()
        except ValueError:
            return None
