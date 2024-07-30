from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from sqlite3 import Cursor, Row


class RawPartialSlot(TypedDict):
    starts_at: datetime
    ends_at: datetime

    section_id: int

    task_id: int | None
    train_id: int | None


class RawSlot(RawPartialSlot):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialSlot:
    starts_at: datetime
    ends_at: datetime

    section_id: int

    task_id: int | None = None
    train_id: int | None = None


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
    def insert_many(cur: Cursor, slots: Iterable[PartialSlot]) -> None:
        payload = [cast(RawPartialSlot, asdict(slot)) for slot in slots]

        cur.executemany(
            """
            INSERT INTO slot (starts_at, ends_at, section_id, task_id, train_id)
            VALUES (:starts_at, :ends_at, :section_id, :task_id, :train_id)
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawSlot) -> Slot:
        return Slot(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM slot")
