from typing import Iterable

from asyncpg import Connection, Record

from train.models.node import Node, PartialNode


class NodeRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> Node | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT node.* FROM node
            WHERE
                node.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return Node.decode(row)

    @staticmethod
    async def find_all(con: Connection) -> list[Node]:
        rows: list[Record] = await con.fetch(
            """
            SELECT node.* FROM node
            """,
        )

        return [Node.decode(row) for row in rows]

    @staticmethod
    async def insert_one(con: Connection, node: PartialNode) -> Node:
        row: Record = await con.fetchrow(
            """
            INSERT INTO node
                (name, position)
            VALUES
                ($1, $2)
            RETURNING *
            """,
            *node.encode()[1:],
        )

        return Node.decode(row)

    @staticmethod
    async def insert_many(con: Connection, nodes: Iterable[PartialNode]) -> list[Node]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO node
                (name, position)
            (
                SELECT n.name, n.position
                FROM unnest($1::node[]) as n
            )
            RETURNING *
            """,
            [node.encode() for node in nodes],
        )

        return [Node.decode(row) for row in rows]
