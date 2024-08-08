from collections.abc import Iterable

from asyncpg import Connection, Record

from train.models.requested_task import RequestedTask
from train.schemas.requested_task import HydratedRequestedTask


class RequestedTaskRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> HydratedRequestedTask | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT
                task.*,
                requested_task.priority,
                requested_task.section_id
            FROM requested_task
            JOIN task
                ON task.id = requested_task.id
            WHERE
                requested_task.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return HydratedRequestedTask.decode(row)

    @staticmethod
    async def find_many_by_ids(
        con: Connection,
        ids: list[int],
    ) -> list[HydratedRequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            SELECT
                task.*,
                requested_task.priority,
                requested_task.section_id
            FROM requested_task
            JOIN task
                ON task.id = requested_task.id
            WHERE
                task.id = any($1::int[])
            """,
            ids,
        )

        return [HydratedRequestedTask.decode(row) for row in rows]

    @staticmethod
    async def find_all(con: Connection) -> list[HydratedRequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            SELECT
                task.*,
                requested_task.priority,
                requested_task.section_id
            FROM requested_task
            JOIN task
                ON task.id = requested_task.id
            """,
        )

        return [HydratedRequestedTask.decode(row) for row in rows]

    @staticmethod
    async def delete_one_by_id(
        con: Connection,
        id: int,
    ) -> HydratedRequestedTask | None:
        row: Record | None = await con.fetchrow(
            """
            DELETE FROM requested_task
            USING task
            WHERE
                task.id = $1
            RETURNING
                task.*,
                requested_task.priority,
                requested_task.section_id
            """,
            id,
        )

        if row is None:
            return None

        return HydratedRequestedTask.decode(row)

    @staticmethod
    async def insert_one(
        con: Connection,
        requested_task: RequestedTask,
    ) -> HydratedRequestedTask:
        row: Record = await con.fetchrow(
            """
            WITH r AS (
                INSERT INTO requested_task
                    (id, priority, section_id)
                VALUES
                    ($1, $2, $3)
                RETURNING *
            )
            SELECT
                task.*,
                r.priority,
                r.section_id
            FROM r
            JOIN task
                ON r.id = task.id
            """,
            *requested_task.encode(),
        )

        return HydratedRequestedTask.decode(row)

    @staticmethod
    async def update_one(
        con: Connection,
        requested_task: RequestedTask,
    ) -> HydratedRequestedTask:
        row: Record = await con.fetchrow(
            """
            WITH r AS (
                UPDATE requested_task SET
                    (priority, section_id) = ($2, $3)
                WHERE
                    requested_task.id = $1
                RETURNING *
            )
            SELECT
                task.*,
                r.priority,
                r.section_id
            FROM r
            JOIN task
                ON r.id = task.id
            """,
            *requested_task.encode(),
        )

        return HydratedRequestedTask.decode(row)

    @staticmethod
    async def insert_many(
        con: Connection,
        requested_tasks: Iterable[RequestedTask],
    ) -> list[HydratedRequestedTask]:
        rows: list[Record] = await con.fetch(
            """
            WITH r AS (
                INSERT INTO requested_task
                    (id, priority, section_id)
                (
                    SELECT
                        t.id, t.priority, t.section_id
                    FROM unnest($1::requested_task[]) as t
                )
                RETURNING *
            )
            SELECT
                task.*,
                r.priority,
                r.section_id
            FROM r
            JOIN task
                ON r.id = task.id
            """,
            [requested_task.encode() for requested_task in requested_tasks],
        )

        return [HydratedRequestedTask.decode(row) for row in rows]
