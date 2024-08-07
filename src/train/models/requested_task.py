from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class RequestedTask(Struct, kw_only=True, frozen=True):
    id: int

    priority: int
    section_id: int

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
