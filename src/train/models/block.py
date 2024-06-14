from __future__ import annotations

from dataclasses import dataclass
from typing import Self, TypeAlias

from train.db import cur

RawBlock: TypeAlias = tuple[int, str]


@dataclass(frozen=True)
class Block:
    id: int
    name: str

    @classmethod
    def find_by_id(cls, id: int) -> Self | None:
        payload = {"id": id}

        res = cur.execute(
            """
            SELECT block.* FROM block
            WHERE
                block.id = :id
            """,
            payload,
        )

        return cls.decode(res.fetchone())

    @classmethod
    def find_by_name(cls, name: str) -> Self | None:
        payload = {"name": name}

        res = cur.execute(
            """
            SELECT block.* FROM block
            WHERE
                block.name = :name
            """,
            payload,
        )

        return cls.decode(res.fetchone())

    @classmethod
    def decode(cls, raw: RawBlock | None) -> Self | None:
        if raw is None:
            return None

        id, name = raw
        return cls(id, name)

    @staticmethod
    def init() -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS block (
                id INTEGER PRIMARY KEY,
                name VARCHAR(25) NOT NULL,

                UNIQUE(name)
            )
            """,
        )
