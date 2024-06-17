from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from heapq import heapify, heappop, heappush
from typing import TYPE_CHECKING, Self, TypeAlias

from train.db import cur

if TYPE_CHECKING:
    from train.models.maintenance_window import MaintenanceWindow

RawTask: TypeAlias = tuple[int, str, str, int, int, int]


@dataclass
class TaskQ:
    priority: int
    requested_duration: timedelta
    starts_at: datetime = field(default=datetime.now())

    def __lt__(self, other: Self) -> bool:
        if self.priority == other.priority:
            return self.starts_at < other.starts_at

        return self.priority > other.priority


@dataclass(frozen=True)
class Task:
    id: int
    starts_at: datetime
    ends_at: datetime
    requested_duration: timedelta
    priority: int

    maintenance_window_id: int

    def maintenance_window(self) -> MaintenanceWindow:
        from train.models.maintenance_window import MaintenanceWindow

        maintenance_window = MaintenanceWindow.find_by_id(self.maintenance_window_id)
        assert maintenance_window is not None

        return maintenance_window

    @classmethod
    def insert_one(  # noqa: PLR0913
        cls,
        starts_at: datetime,
        ends_at: datetime,
        requested_duration: timedelta,
        priority: int,
        maintenance_window_id: int,
    ) -> Self:
        payload = {
            "starts_at": starts_at,
            "ends_at": ends_at,
            "requested_duration": requested_duration,
            "priority": priority,
            "maintenance_window_id": maintenance_window_id,
        }

        res = cur.execute(
            """
            INSERT INTO task (
                starts_at,
                ends_at,
                requested_duration,
                priority,
                maintenance_window_id
            ) VALUES (
                :starts_at,
                :ends_at,
                :requested_duration,
                :priority,
                :maintenance_window_id
            ) RETURNING *
            """,
            payload,
        )

        task = cls.decode(res.fetchone())
        assert task is not None

        return task

    @classmethod
    def insert_greedy(
        cls,
        requested_duration: timedelta,
        priority: int,
        section_id: int,
    ) -> list[Self]:
        queue: list[TaskQ] = [TaskQ(priority, requested_duration)]
        heapify(queue)

        tasks: list[Self] = []
        while queue:
            taskq = heappop(queue)

            payload = {
                "requested_duration": taskq.requested_duration,
                "priority": taskq.priority,
                "section_id": section_id,
            }

            res = cur.execute(
                """
                SELECT IFNULL(
                    (
                        SELECT task.ends_at FROM task
                        WHERE
                            task.maintenance_window_id = maintenance_window.id
                            AND task.priority >= :priority
                        ORDER BY
                            task.ends_at DESC
                        LIMIT 1
                    ),
                    maintenance_window.starts_at
                ) AS k, maintenance_window.id
                FROM maintenance_window
                WHERE
                    maintenance_window.section_id = :section_id
                    AND maintenance_window.starts_at >= DATETIME('now', '+30 minutes')
                    AND UNIXEPOCH(maintenance_window.ends_at) - UNIXEPOCH(k)
                        >= :requested_duration
                ORDER BY
                    K ASC
                LIMIT 1
                """,
                payload,
            )

            x = res.fetchone()
            if x is None:
                print("NO TIME SLOT FOR DURATION :(")
                raise Exception  # noqa: TRY002

            starts_at, maintenance_window_id = x
            starts_at = datetime.fromisoformat(starts_at)
            ends_at = starts_at + taskq.requested_duration

            payload = {
                "maintenance_window_id": maintenance_window_id,
                "starts_at": starts_at,
                "ends_at": ends_at,
            }

            res = cur.execute(
                """
                DELETE FROM task
                WHERE
                    maintenance_window_id = :maintenance_window_id
                    AND starts_at >= :starts_at
                    AND starts_at < :ends_at
                RETURNING requested_duration, priority, starts_at
                """,
                payload,
            )

            for dur, pr, st in res.fetchall():
                heappush(
                    queue,
                    TaskQ(pr, timedelta(minutes=dur), datetime.fromisoformat(st)),
                )

            task = cls.insert_one(
                starts_at,
                ends_at,
                taskq.requested_duration,
                taskq.priority,
                maintenance_window_id,
            )

            tasks.append(task)

        return tasks

    @classmethod
    def insert_preferred(
        cls,
        preferred_starts_at: time,
        preferred_ends_at: time,
        priority: int,
        section_id: int,
    ) -> list[Self]:
        requested_duration = (
            datetime.combine(date.min, preferred_ends_at)
            - datetime.combine(date.min, preferred_starts_at)
            + (preferred_ends_at < preferred_starts_at) * timedelta(hours=24)
        )

        payload = {
            "requested_duration": requested_duration,
            "priority": priority,
            "section_id": section_id,
        }

        cur.execute(
            """
                SELECT IFNULL(
                    (
                        SELECT task.ends_at FROM task
                        WHERE
                            task.maintenance_window_id = maintenance_window.id
                            AND task.priority >= :priority
                        ORDER BY
                            task.ends_at DESC
                        LIMIT 1
                    ),
                    maintenance_window.starts_at
                ) AS k,
                UNIXEPOCH(:preferred_starts_at) -
                    86400 * (:preferred_ends_at < preferred_starts_at)
                    AS p_starts,
                UNIXEPOCH(:preferred_ends_at) AS p_ends,
                UNIXEPOCH(TIME(k)) -
                    86400 * (TIME(maintenance_window.ends_at) < TIME(k))
                    AS m_starts,
                UNIXEPOCH(TIME(maintenance_window.ends_at)) AS m_ends,
                maintenance_window.id
                FROM maintenance_window
                WHERE
                    maintenance_window.section_id = :section_id
                    AND maintenance_window.starts_at >= DATETIME('now', '+30 minutes')
                    AND UNIXEPOCH(maintenance_window.ends_at) - UNIXEPOCH(k)
                        >= :requested_duration
                ORDER BY
                    MAX(
                        (p_ends - p_starts)
                        - MAX(p_ends - m_ends, 0)
                        - MAX(m_starts - p_starts, 0),
                        (p_ends - p_starts)
                        - MAX(p_ends - m_ends + 86400, 0)
                        - MAX(m_starts - p_starts - 86400, 0),
                        (p_ends - p_starts)
                        - MAX(p_ends - m_ends - 86400, 0)
                        - MAX(m_starts - p_starts + 86400, 0)
                    )
                LIMIT 1
                """,
            payload,
        )

        return []

    @classmethod
    def find_by_id(cls, id: int) -> Self | None:
        payload = {"id": id}

        res = cur.execute(
            """
            SELECT task.* FROM task
            WHERE
                task.id = :id
            """,
            payload,
        )

        raw = res.fetchone()
        if raw is None:
            return None

        return cls.decode(res.fetchone())

    @classmethod
    def decode(cls, raw: RawTask) -> Self:
        (
            id,
            starts_at,
            ends_at,
            requested_duration,
            priority,
            maintenance_window_id,
        ) = raw

        return cls(
            id,
            datetime.fromisoformat(starts_at),
            datetime.fromisoformat(ends_at),
            timedelta(minutes=requested_duration),
            priority,
            maintenance_window_id,
        )

    @staticmethod
    def init() -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY,
                starts_at DATETIME NOT NULL,
                ends_at DATETIME NOT NULL,
                requested_duration INTEGER NOT NULL,
                priority INTEGER NOT NULL,

                maintenance_window_id INTEGER NOT NULL,
                FOREIGN KEY(maintenance_window_id) REFERENCES maintenance_window(id)
            )
            """,
        )

    @classmethod
    def delete_future_tasks(cls, section_id: int) -> list[Self]:
        payload = {"section_id": section_id}

        res = cur.execute(
            """
            DELETE FROM task
            WHERE
                id in (
                    SELECT task.id FROM task
                    JOIN maintenance_window ON
                        maintenance_window.id = task.maintenance_window_id
                    JOIN section ON
                        section.id = maintenance_window.section_id
                    WHERE
                        section.id = :section_id
                        AND task.starts_at >= DATETIME('now', '+30 minutes')
                )
            RETURNING *
            """,
            payload,
        )

        return [cls.decode(raw) for raw in res.fetchall()]
