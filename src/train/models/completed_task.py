from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class CompletedTask(Struct, kw_only=True, frozen=True):
    id: int

    output: int

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
