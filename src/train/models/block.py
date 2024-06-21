from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


@dataclass(frozen=True)
class PartialBlock:
    name: str


@dataclass(frozen=True)
class Block:
    id: int
    name: str

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Block | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT block.* FROM block
            WHERE
                block.id = :id
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return Block.decode(raw)

    @staticmethod
    def find_by_name(cur: Cursor, name: str) -> Block | None:
        payload = {"name": name}

        cur.execute(
            """
            SELECT block.* FROM block
            WHERE
                block.name = :name
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Block.decode(row)

    @staticmethod
    def insert_many(cur: Cursor, blocks: Iterable[PartialBlock]) -> None:
        payload = [{"name": block.name} for block in blocks]

        cur.executemany(
            """
            INSERT INTO block (name)
            VALUES (:name)
            ON CONFLICT DO NOTHING
            """,
            payload,
        )

    @staticmethod
    def decode(row: Row) -> Block:
        return Block(row["id"], row["name"])
