from collections import defaultdict
from collections.abc import Iterable

from asyncpg import Connection, Record

from src.train.models.slot import Slot
from src.train.schemas.requested_task import HydratedRequestedTask
from src.train.schemas.task import HydratedTask
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
    async def find_all_scheduled(con: Connection) -> list[HydratedTask]:
        rows: list[Record] = await con.fetch(
            """
            SELECT
                task.*,
                requested_task.priority,
                requested_task.section_id
            FROM task
            JOIN requested_task
                ON task.id = requested_task.id
            """,
        )

        tasks = [HydratedRequestedTask.decode(row) for row in rows]

        rows: list[Record] = await con.fetch(
            """
            SELECT slot.* FROM slot
            WHERE task_id IS NOT NULL
            """,
        )

        slots = [Slot.decode(row) for row in rows]
        slots_by_task = defaultdict(list)
        for slot in slots:
            slots_by_task[slot.task_id].append(slot)

        return [
            HydratedTask.decode((*task.encode(), slots_by_task[task.id]))
            for task in tasks
            if task.id in slots_by_task
        ]

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
            *task.encode()[1:10],
        )

        return Task.decode(row)

    @staticmethod
    async def update_one(con: Connection, task: Task) -> Task | None:
        row: Record | None = await con.fetchrow(
            """
            UPDATE task SET
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
            ) = ($2, $3, $4, $5, $6, $7, $8, $9, $10)
            WHERE
                task.id = $1
            RETURNING *
            """,
            *task.encode()[:10],
        )

        if row is None:
            return None

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
            [task.encode()[:10] for task in tasks],
        )

        return [Task.decode(row) for row in rows]
