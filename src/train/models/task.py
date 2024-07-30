from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date, datetime, time, timedelta
    from sqlite3 import Cursor, Row


class RawPartialTask(TypedDict):
    department: str
    den: str
    nature_of_work: str
    location: str

    starts_at: datetime
    ends_at: datetime

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    priority: int


class RawTask(RawPartialTask):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialTask:
    department: str
    den: str
    nature_of_work: str
    location: str

    starts_at: datetime
    ends_at: datetime

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    priority: int


@dataclass(frozen=True)
class Task(PartialTask):
    id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Task | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT task.* FROM task
            WHERE
                task.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Task.decode(cast(RawTask, row))

    @staticmethod
    def insert_many(cur: Cursor, tasks: Iterable[PartialTask]) -> None:
        payload = [cast(RawPartialTask, asdict(task)) for task in tasks]

        cur.executemany(
            """
            INSERT INTO task (
                department,
                den,
                nature_of_work,
                location,
                starts_at,
                ends_at,
                preferred_starts_at,
                preferred_ends_at,
                requested_date,
                requested_duration,
                priority
            )
            VALUES (
                :department,
                :den,
                :nature_of_work,
                :location,
                :starts_at,
                :ends_at,
                :preferred_starts_at,
                :preferred_ends_at,
                :requested_date,
                :requested_duration,
                :priority
            )
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawTask) -> Task:
        return Task(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM task")
