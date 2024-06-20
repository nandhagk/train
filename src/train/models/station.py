from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from train.db import cur

RawStation: TypeAlias = tuple[int, str, int]


@dataclass(frozen=True)
class Station:
    id: int
    name: str

    block_id: int

    @staticmethod
    def find_by_id(id: int) -> Station | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.id = :id
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return Station.decode(raw)

    @staticmethod
    def find_by_name(name: str) -> Station | None:
        payload = {"name": name}

        cur.execute(
            """
            SELECT station.* FROM station
            WHERE
                station.name = :name
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return Station.decode(raw)

    @staticmethod
    def insert_many(station_names: list[str], block_id: int) -> None:
        payload = [{"name": name, "block_id": block_id} for name in station_names]

        cur.executemany(
            """
            INSERT INTO station (name, block_id)
            VALUES (:name, :block_id)
            ON CONFLICT DO NOTHING
            """,
            payload,
        )

    @staticmethod
    def decode(raw: RawStation) -> Station:
        id, name, block_id = raw
        return Station(id, name, block_id)

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
