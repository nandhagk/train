from typing import Iterable

from asyncpg import Connection, Record

from train.models.task import PartialTask, Task


class TaskRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> Task | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT task.* FROM task
            WHERE
                task.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return Task.decode(row)

    @staticmethod
    async def find_all(con: Connection) -> list[Task]:
        rows: list[Record] = await con.fetch(
            """
            SELECT task.* FROM task
            """,
        )

        return [Task.decode(row) for row in rows]

    @staticmethod
    async def insert_one(con: Connection, task: PartialTask) -> Task:
        row: Record = await con.fetchrow(
            """
            INSERT INTO task
            (
                department,
                den,
                nature_of_work,
                block,
                location,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration
            )
            VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            *task.encode()[1:],
        )

        return Task.decode(row)

    @staticmethod
    async def insert_many(con: Connection, tasks: Iterable[PartialTask]) -> list[Task]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO task
            (
                department,
                den,
                nature_of_work,
                block,
                location,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration
            )
            (
                SELECT
                    t.department,
                    t.den,
                    t.nature_of_work,
                    t.block,
                    t.location,
                    t.preferred_starts_at,
                    t.preferred_ends_at,
                    t.requested_date,
                    t.requested_duration
                FROM unnest($1::task[]) as t
            )
            RETURNING *
            """,
            [task.encode()[:10] for task in tasks],  # TaskToInsert or PartialRequested
        )

        return [Task.decode(row) for row in rows]
