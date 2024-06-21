from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from train.db import cur

if TYPE_CHECKING:
    from collections.abc import Iterable

RawBlock: TypeAlias = tuple[int, str]


@dataclass(frozen=True)
class PartialBlock:
    name: str


@dataclass(frozen=True)
class Block:
    id: int
    name: str

    @staticmethod
    def find_by_id(id: int) -> Block | None:
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
    def find_by_name(name: str) -> Block | None:
        payload = {"name": name}

        cur.execute(
            """
            SELECT block.* FROM block
            WHERE
                block.name = :name
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return Block.decode(raw)

    @staticmethod
    def insert_many(blocks: Iterable[PartialBlock]) -> None:
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
    def decode(raw: RawBlock) -> Block:
        id, name = raw
        return Block(id, name)
