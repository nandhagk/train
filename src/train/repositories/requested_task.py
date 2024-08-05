from collections.abc import Iterable

from asyncpg import Connection, Record

from train.models.requested_task import PartialRequestedTask, RequestedTask


class RequestedTaskRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> RequestedTask | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT requested_requested_task.* FROM requested_task
            WHERE
                requested_task.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return RequestedTask.decode(row)

    @staticmethod
    async def find_many_by_ids(con: Connection, ids: list[int]) -> list[RequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            SELECT requested_task.* FROM requested_task
            WHERE
                requested_task.id = any($1::int[])
            """,
            ids,
        )

        return [RequestedTask.decode(row) for row in rows]

    @staticmethod
    async def find_all(con: Connection) -> list[RequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            SELECT requested_task.* FROM requested_task
            """,
        )

        return [RequestedTask.decode(row) for row in rows]

    @staticmethod
    async def delete_one_by_id(con: Connection, id: int) -> RequestedTask | None:
        row: Record | None = await con.fetchrow(
            """
            DELETE FROM requested_task
            WHERE
                requested_task.id = $1
            RETURNING *
            """,
            id,
        )

        if row is None:
            return None

        return RequestedTask.decode(row)

    @staticmethod
    async def insert_one(
        con: Connection,
        requested_task: PartialRequestedTask,
    ) -> RequestedTask:
        row: Record = await con.fetchrow(
            """
            INSERT INTO requested_task
            (
                department,
                den,
                nature_of_work,
                block,
                location,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration,
                priority,
                section_id
            )
            VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
            """,
            *requested_task.encode()[1:],
        )

        return RequestedTask.decode(row)

    @staticmethod
    async def update_one(
        con: Connection,
        requested_task: RequestedTask,
    ) -> RequestedTask:
        row: Record = await con.fetchrow(
            """
            UPDATE requested_task SET
            (
                department,
                den,
                nature_of_work,
                block,
                location,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration,
                priority,
                section_id
            ) = ($2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            WHERE
                requested_task.id = $1
            RETURNING *
            """,
            *requested_task.encode(),
        )

        return RequestedTask.decode(row)

    @staticmethod
    async def insert_many(
        con: Connection,
        requested_tasks: Iterable[PartialRequestedTask],
    ) -> list[RequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO requested_task
            (
                department,
                den,
                nature_of_work,
                block,
                location,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration,
                priority,
                section_id
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
                    t.requested_duration,
                    t.priority,
                    t.section_id
                FROM unnest($1::requested_task[]) as t
            )
            RETURNING *
            """,
            [requested_task.encode() for requested_task in requested_tasks],
        )

        return [RequestedTask.decode(row) for row in rows]
