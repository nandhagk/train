from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


class RawPartialTrain(TypedDict):
    name: str
    number: str


class RawTrain(RawPartialTrain):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialTrain:
    name: str
    number: str


@dataclass(frozen=True)
class Train(PartialTrain):
    id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Train | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT train.* FROM train
            WHERE
                train.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Train.decode(cast(RawTrain, row))

    @staticmethod
    def insert_many(cur: Cursor, trains: Iterable[PartialTrain]) -> None:
        payload = [cast(RawPartialTrain, asdict(train)) for train in trains]

        cur.executemany(
            """
            INSERT INTO train (name, number)
            VALUES (:name, :number)
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawTrain) -> Train:
        return Train(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM train")
