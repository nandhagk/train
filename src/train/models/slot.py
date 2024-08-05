from datetime import datetime
from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class PartialSlot(Struct, kw_only=True, frozen=True):
    id: None = None

    starts_at: datetime
    ends_at: datetime

    priority: int
    section_id: int

    task_id: int | None
    train_id: int | None

    def __post_init__(self: Self) -> None:
        if (self.task_id is None) ^ (self.train_id is None):
            return

        msg = "Exactly one of 'task_id`' or 'train_id' must be set."
        raise ValueError(msg)

    def encode(self) -> tuple:
        return astuple(self)


class Slot(Struct, kw_only=True, frozen=True):
    id: int

    starts_at: datetime
    ends_at: datetime

    priority: int
    section_id: int

    task_id: int | None
    train_id: int | None

    def __post_init__(self: Self) -> None:
        if (self.task_id is None) ^ (self.train_id is None):
            return

        msg = "Exactly one of 'task_id`' or 'train_id' must be set."
        raise ValueError(msg)

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
