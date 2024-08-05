from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class PartialSection(Struct, kw_only=True, frozen=True):
    id: None = None

    line: str

    from_id: int
    to_id: int

    def encode(self) -> tuple:
        return astuple(self)


class Section(Struct, kw_only=True, frozen=True):
    id: int

    line: str

    from_id: int
    to_id: int

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
