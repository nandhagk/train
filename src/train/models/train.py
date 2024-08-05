from typing import Self

from asyncpg import Record
from msgspec import Struct
from msgspec.structs import astuple


class PartialTrain(Struct, kw_only=True, frozen=True):
    id: None = None

    name: str
    number: str

    def encode(self) -> tuple:
        return astuple(self)


class Train(Struct, kw_only=True, frozen=True):
    id: int

    name: str
    number: str

    def encode(self) -> tuple:
        return astuple(self)

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)
