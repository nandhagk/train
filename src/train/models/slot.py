from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from sqlite3 import Cursor, Row

    from train.services.slot import TaskSlotToInsert


class RawPartialSlot(TypedDict):
    starts_at: datetime
    ends_at: datetime
    priority: int

    section_id: int

    task_id: int | None
    train_id: int | None


class RawSlot(RawPartialSlot):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialSlot:
    starts_at: datetime
    ends_at: datetime
    priority: int

    section_id: int

    task_id: int | None
    train_id: int | None


@dataclass(frozen=True)
class Slot(PartialSlot):
    id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Slot | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT slot.* FROM slot
            WHERE
                slot.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Slot.decode(cast(RawSlot, row))

    @staticmethod
    def find_fixed_slots(
        cur: Cursor,
        section_id: int,
        priority: int,
        after: datetime,
    ) -> list[Slot]:
        payload = {"section_id": section_id, "priority": priority, "after": after}

        cur.execute(
            """
            SELECT slot.* FROM slot
            WHERE
                slot.section_id = :section_id
                AND slot.priority >= :priority
                AND slot.ends_at >= :after
            ORDER BY
                slot.starts_at ASC
            """,
            payload,
        )

        rows: list[Row] = cur.fetchall()
        return [Slot.decode(cast(RawSlot, row)) for row in rows]

    @staticmethod
    def pop_intersecting_slots(
        cur: Cursor,
        section_id: int,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[TaskSlotToInsert]:
        from train.services.slot import RawTaskSlotToInsert, TaskSlotToInsert

        payload = {"starts_at": starts_at, "ends_at": ends_at, "section_id": section_id}

        cur.execute(
            """
            SELECT
                slot.*,
                task.preferred_starts_at,
                task.preferred_ends_at,
                task.requested_date,
                task.requested_duration
            FROM slot
            JOIN task
                ON task.id = slot.task_id
            WHERE
                slot.section_id = :section_id
                AND slot.starts_at <= :ends_at
                AND slot.ends_at >= :starts_at
            """,
            payload,
        )

        rows: list[Row] = cur.fetchall()
        slots = [
            TaskSlotToInsert.decode(cast(RawTaskSlotToInsert, row)) for row in rows
        ]

        cur.execute(
            """
            DELETE FROM slot
            WHERE
                slot.section_id = :section_id
                AND slot.starts_at <= :ends_at
                AND slot.ends_at >= :starts_at
            """,
            payload,
        )

        return slots

    @staticmethod
    def insert_one(cur: Cursor, slot: PartialSlot) -> Slot:
        payload = cast(RawPartialSlot, asdict(slot))

        cur.execute(
            """
            INSERT INTO slot (
                starts_at,
                ends_at,
                priority,
                section_id,
                task_id,
                train_id
            )
            VALUES (
                :starts_at,
                :ends_at,
                :priority,
                :section_id,
                :task_id,
                :train_id
            )
            """,
            payload,
        )

        row: Row = cur.fetchone()
        return Slot.decode(cast(RawSlot, row))

    @staticmethod
    def insert_many(cur: Cursor, slots: Iterable[PartialSlot]) -> None:
        payload = [cast(RawPartialSlot, asdict(slot)) for slot in slots]

        cur.executemany(
            """
            INSERT INTO slot (
                starts_at,
                ends_at,
                priority,
                section_id,
                task_id,
                train_id
            )
            VALUES (
                :starts_at,
                :ends_at,
                :priority,
                :section_id,
                :task_id,
                :train_id
            )
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawSlot) -> Slot:
        return Slot(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM slot")
