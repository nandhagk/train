from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, TypeAlias

from train.db import cur

if TYPE_CHECKING:
    from train.models.block import Block

RawStation: TypeAlias = tuple[int, str, int]


@dataclass(frozen=True)
class Station:
    id: int
    name: str

    block_id: int

    def block(self) -> Block:
        from train.models.block import Block

        block = Block.find_by_id(self.block_id)
        assert block is not None

        return block

    @classmethod
    def find_by_id(cls, id: int) -> Self | None:
        payload = {"id": id}
        res = cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.id = :id
            """,
            payload,
        )

        return cls.decode(res.fetchone())

    @classmethod
    def find_by_name(cls, name: str) -> Self | None:
        res = cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.name = :name
            """,
            {"name": name},
        )

        return cls.decode(res.fetchone())

    @classmethod
    def decode(cls, raw: RawStation | None) -> Self | None:
        if raw is None:
            return None

        id, name, block_id = raw
        return cls(id, name, block_id)

    @staticmethod
    def init() -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS station (
                id INTEGER PRIMARY KEY,
                name VARCHAR(25) NOT NULL,

                block_id INTEGER NOT NULL,
                FOREIGN KEY(block_id) REFERENCES block(id),

                UNIQUE(name)
            )
            """,
        )

    @staticmethod
    def insert_many(stations: list[str], block_id: int) -> None:
        cur.executemany(
            """
            INSERT INTO station (id, name, block_id)
            VALUES (NULL, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            [(station, block_id) for station in stations],
        )
