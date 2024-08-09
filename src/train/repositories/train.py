from collections.abc import Iterable

from asyncpg import Connection, Record

from train.models.train import PartialTrain, Train


class TrainRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> Train | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT train.* FROM train
            WHERE
                train.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return Train.decode(row)

    @staticmethod
    async def find_one_by_number(con: Connection, number: str) -> Train | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT train.* FROM train
            WHERE
                train.number = $1
            """,
            number,
        )

        if row is None:
            return None

        return Train.decode(row)

    @staticmethod
    async def find_all(con: Connection) -> list[Train]:
        rows: list[Record] = await con.fetch(
            """
            SELECT train.* FROM train
            """,
        )

        return [Train.decode(row) for row in rows]

    @staticmethod
    async def insert_one(con: Connection, train: PartialTrain) -> Train:
        row: Record = await con.fetchrow(
            """
            INSERT INTO train
                (name, number)
            VALUES
                ($1, $2)
            RETURNING *
            """,
            *train.encode()[1:],
        )

        return Train.decode(row)

    @staticmethod
    async def insert_many(
        con: Connection,
        trains: Iterable[PartialTrain],
    ) -> list[Train]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO train
                (name, number)
            (
                SELECT t.name, t.number
                FROM unnest($1::train[]) as t
            )
            RETURNING *
            """,
            [train.encode() for train in trains],
        )

        return [Train.decode(row) for row in rows]
