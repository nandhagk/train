from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


@dataclass(frozen=True)
class PartialStation:
    name: str

    block_id: int


@dataclass(frozen=True)
class Station:
    id: int
    name: str

    block_id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Station | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Station.decode(row)

    @staticmethod
    def find_by_name(cur: Cursor, name: str) -> Station | None:
        payload = {"name": name}

        cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.name = :name
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Station.decode(row)

    @staticmethod
    def insert_many(cur: Cursor, stations: Iterable[PartialStation]) -> None:
        payload = [
            {"name": station.name, "block_id": station.block_id} for station in stations
        ]

        cur.executemany(
            """
            INSERT INTO station (name, block_id)
            VALUES (:name, :block_id)
            ON CONFLICT DO NOTHING
            """,
            payload,
        )

    @staticmethod
    def decode(row: Row) -> Station:
        return Station(row["id"], row["name"], row["block_id"])
