from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


class RawPartialNode(TypedDict):
    name: str
    position: int


class RawNode(RawPartialNode):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialNode:
    name: str
    position: int


@dataclass(frozen=True)
class Node(PartialNode):
    id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Node | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT node.* FROM node
            WHERE
                node.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Node.decode(cast(RawNode, row))

    @staticmethod
    def find_all(cur: Cursor) -> list[Node]:
        cur.execute("SELECt node.* FROM node")

        rows: list[Row] = cur.fetchall()
        return [Node.decode(cast(RawNode, row)) for row in rows]

    @staticmethod
    def insert_many(cur: Cursor, nodes: Iterable[PartialNode]) -> None:
        payload = [cast(RawPartialNode, asdict(node)) for node in nodes]

        cur.executemany(
            """
            INSERT INTO node (name, position)
            VALUES (:name, :position)
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawNode) -> Node:
        return Node(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM node")
