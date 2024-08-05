from datetime import datetime
from typing import TYPE_CHECKING, Iterable

from asyncpg import Connection, Record

from train.models.slot import PartialSlot, Slot

if TYPE_CHECKING:
    from train.services.slot import TaskSlotToInsert


class SlotRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> Slot | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT slot.* FROM slot
            WHERE
                slot.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return Slot.decode(row)

    @staticmethod
    async def find_fixed(
        con: Connection,
        priority: int,
        section_id: int,
        after: datetime,
    ) -> list[Slot]:
        rows: list[Record] = await con.fetch(
            """
            SELECT slot.* FROM slot
            WHERE
                slot.priority >= $1
                AND slot.section_id = $2
                AND slot.ends_at >= $3
            ORDER BY
                slot.starts_at ASC
            """,
            priority,
            section_id,
            after,
        )

        return [Slot.decode(row) for row in rows]

    @staticmethod
    async def find_all(con: Connection) -> list[Slot]:
        rows: list[Record] = await con.fetch(
            """
            SELECT slot.* FROM slot
            """,
        )

        return [Slot.decode(row) for row in rows]

    @staticmethod
    async def pop_intersecting(
        con: Connection,
        priority: int,
        section_id: int,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list["TaskSlotToInsert"]:
        from train.services.slot import TaskSlotToInsert

        rows: list[Record] = await con.fetch(
            """
            DELETE FROM slot USING task
            WHERE
                task.id = slot.task_id
                AND slot.priority < $1
                AND slot.section_id = $2
                AND slot.starts_at < $4
                AND slot.ends_at > $3
            RETURNING
                slot.priority,
                slot.task_id,
                task.preferred_starts_at,
                task.preferred_ends_at,
                task.requested_date,
                task.requested_duration
            """,
            priority,
            section_id,
            starts_at,
            ends_at,
        )

        return [TaskSlotToInsert.decode(row) for row in rows]

    @staticmethod
    async def insert_one(con: Connection, slot: PartialSlot) -> Slot:
        row: Record = await con.fetchrow(
            """
            INSERT INTO slot
                (starts_at, ends_at, priority, section_id, task_id, train_id)
            VALUES
                ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            *slot.encode()[1:],
        )

        return Slot.decode(row)

    @staticmethod
    async def insert_many(con: Connection, slots: Iterable[PartialSlot]) -> list[Slot]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO slot
                (starts_at, ends_at, priority, section_id, task_id, train_id)
            (
                SELECT
                    s.starts_at,
                    s.ends_at,
                    s.priority,
                    s.section_id,
                    s.task_id,
                    s.train_id
                FROM unnest($1::slot[]) as s
            )
            RETURNING *
            """,
            [slot.encode() for slot in slots],
        )

        return [Slot.decode(row) for row in rows]
