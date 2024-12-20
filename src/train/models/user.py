from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class PartialUser(Struct, kw_only=True, frozen=True):
    id: int | None = None

    name: str

    def encode(self) -> tuple:
        return astuple(self)


class User(Struct, kw_only=True, frozen=True):
    id: int

    name: str

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
