from datetime import date, time, timedelta
from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class PartialTask(Struct, frozen=True, kw_only=True):
    id: None = None

    department: str
    den: str
    nature_of_work: str
    block: str
    location: str

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    def encode(self) -> tuple:
        return astuple(self)


class Task(Struct, frozen=True, kw_only=True):
    id: int

    department: str
    den: str
    nature_of_work: str
    block: str
    location: str

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
