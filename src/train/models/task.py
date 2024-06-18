from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from heapq import heapify, heappop, heappush
from typing import TYPE_CHECKING, Self, TypeAlias, TypeVar, Generic

from train.db import cur

if TYPE_CHECKING:
    from train.models.maintenance_window import MaintenanceWindow

RawTask: TypeAlias = tuple[int, str, str, str | None, str | None, int, int, int]

T = TypeVar("T", None, time)

@dataclass
class TaskQ(Generic[T]):
    priority: int
    requested_duration: timedelta
    preferred_starts_at: T
    preferred_ends_at: T
    starts_at: datetime = field(default=datetime.now())

    @property
    def preferred_range(self) -> timedelta:
        if self.preferred_starts_at is None or self.preferred_ends_at is None:
            return timedelta(days=1)
        return (
            datetime.combine(date.min, self.preferred_ends_at)
            - datetime.combine(date.min, self.preferred_starts_at)
            + timedelta(days=int(self.preferred_starts_at >= self.preferred_ends_at))
        )

    def __lt__(self, other: Self) -> bool:
        """
        Priority Order.

        Priority (Hi)
        -> Requested Duration (Hi)
        -> Preferred Range (Lo)
        -> Starts At (Lo)
        """
        if self.priority == other.priority:
            if self.requested_duration == other.requested_duration:
                if self.preferred_range == other.preferred_range:
                    return self.starts_at < other.starts_at
                return self.preferred_range < other.preferred_range
            return self.requested_duration > other.requested_duration
        return self.priority > other.priority

@dataclass(frozen=True)
class Task:
    id: int
    starts_at: datetime
    ends_at: datetime
    preferred_starts_at: time | None
    preferred_ends_at: time | None
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
        preferred_starts_at: time | None = None,
        preferred_ends_at: time | None = None,
    ) -> Self:
        payload = {
            "starts_at": starts_at,
            "ends_at": ends_at,
            "preferred_starts_at": preferred_starts_at,
            "preferred_ends_at": preferred_ends_at,
            "requested_duration": requested_duration,
            "priority": priority,
            "maintenance_window_id": maintenance_window_id,
        }

        res = cur.execute(
            """
            INSERT INTO task (
                starts_at,
                ends_at,
                preferred_starts_at,
                preferred_ends_at,
                requested_duration,
                priority,
                maintenance_window_id
            ) VALUES (
                :starts_at,
                :ends_at,
                :preferred_starts_at,
                :preferred_ends_at,
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
    

    @staticmethod
    def _insert(tasks: list[TaskQ], tasks_to_insert: list[Task], section_id: int) -> list[Task]:
        if not tasks: return tasks_to_insert

        taskq = heappop(tasks)
        if taskq.preferred_ends_at is None and taskq.preferred_starts_at is None:
            window_id, starts_at, ends_at = Task._insert_nopref(taskq, section_id)
        else:
            window_id, starts_at, ends_at = Task._insert_pref(taskq, section_id)
        
        payload = {
            "window_id": window_id,
            "starts_at": starts_at,
            "ends_at": ends_at,
        }
        res = cur.execute(
            """
            DELETE FROM task
            WHERE
                task.maintenance_window_id = :window_id
                AND (
                    (task.starts_at > :starts_at AND task.starts_at < :ends_at)
                    OR (task.ends_at > :starts_at AND task.ends_at < :ends_at)
                    OR (:starts_at > task.starts_at AND :starts_at < task.ends_at)
                )
            RETURNING *
            """,
            payload,
        )
        for taskq in [Task.decode(x) for x in res.fetchall()]:
            heappush(
                tasks,
                TaskQ(
                    taskq.priority,
                    taskq.requested_duration,
                    taskq.preferred_starts_at,
                    taskq.preferred_ends_at,
                    taskq.starts_at,
                ),
            )

        tasks_to_insert.append(
            Task.insert_one(
                starts_at, ends_at,
                taskq.requested_duration, taskq.priority,
                window_id, taskq.preferred_starts_at, taskq.preferred_ends_at
            )
        )

        return Task._insert(tasks, tasks_to_insert, section_id)


    @staticmethod
    def _insert_pref(taskq: TaskQ[time], section_id: int) -> tuple[int, datetime, datetime]:
        payload = {
            "requested_duration": taskq.requested_duration,
            "preferred_starts_at": taskq.preferred_starts_at.isoformat(),
            "preferred_ends_at": taskq.preferred_ends_at.isoformat(),
            "priority": taskq.priority,
            "section_id": section_id,
        }

        print(taskq)
        res = cur.execute(
            """
            SELECT
            UNIXEPOCH(:preferred_starts_at) -
                86400 * (:preferred_ends_at <= :preferred_starts_at)
                AS p_starts,
            UNIXEPOCH(:preferred_ends_at) AS p_ends,
            UNIXEPOCH(TIME(window_start)) -
                86400 * (TIME(window_end) <= TIME(window_start))
                AS m_starts,
            UNIXEPOCH(TIME(window_end)) AS m_ends,
            window_id,
            window_start,
            window_end
            FROM (
                SELECT
                    window_start,
                    COALESCE(
                        (
                            SELECT task.starts_at FROM task
                            JOIN maintenance_window
                                ON task.maintenance_window_id = window_id
                            WHERE
                                task.priority >= :priority
                                AND task.starts_at >= window_start
                            ORDER BY
                                task.starts_at ASC
                            LIMIT 1
                        ),
                        m_window_end
                    ) AS window_end,
                    window_id
                FROM (
                    SELECT
                        maintenance_window.starts_at AS window_start,
                        maintenance_window.ends_at AS m_window_end,
                        maintenance_window.id as window_id,
                        maintenance_window.section_id as section_id
                    FROM maintenance_window
                    UNION
                    SELECT
                        task.ends_at AS window_start,
                        maintenance_window.ends_at AS m_window_end,
                        maintenance_window.id as window_id,
                        maintenance_window.section_id as section_id
                    FROM task
                    JOIN maintenance_window
                        ON maintenance_window.id = task.maintenance_window_id
                    WHERE
                        task.priority >= :priority
                )
                WHERE
                    section_id = :section_id
                    AND window_start >= DATETIME('now', '+30 minutes')
                    AND UNIXEPOCH(window_end) - UNIXEPOCH(window_start)
                        >= :requested_duration
            )
            ORDER BY
                MIN(
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
                    ),
                    :requested_duration
                ) DESC,
                window_start ASC
            LIMIT
                1
            """,
            payload,
        )

        x: (
            tuple[
                int,
                int,
                int,
                int,
                int,
                str,
                str,
            ]
            | None
        ) = res.fetchone()
        if x is None:
            raise Exception  # noqa: TRY002

        (
            p_starts,
            p_ends,
            m_starts,
            m_ends,
            window_id,
            window_start,
            window_end,
        ) = x

        window_start = datetime.fromisoformat(window_start)
        window_end = datetime.fromisoformat(window_end)
        intersection = timedelta(
            seconds=max(
                (p_ends - p_starts)
                - max(p_ends - m_ends, 0)
                - max(m_starts - p_starts, 0),
                (p_ends - p_starts)
                - max(p_ends - m_ends + 86400, 0)
                - max(m_starts - p_starts - 86400, 0),
                (p_ends - p_starts)
                - max(p_ends - m_ends - 86400, 0)
                - max(m_starts - p_starts + 86400, 0),
            ),
        )

        possible_preferred_dates = (
            window_start + timedelta(days=-1),
            window_start,
            window_end,
            window_end + timedelta(days=+1),
        )

        possible_preferred_windows = (
            (
                possible_preferred_date.combine(
                    possible_preferred_date.date(),
                    taskq.preferred_starts_at,
                ),
                possible_preferred_date.combine(
                    possible_preferred_date.date(),
                    taskq.preferred_ends_at,
                )
                + timedelta(
                    days=(
                        1
                        if taskq.preferred_starts_at >= taskq.preferred_ends_at
                        else 0
                    ),
                ),
            )
            for possible_preferred_date in possible_preferred_dates
        )

        closest_preferred_start: datetime
        closest_preferred_end: datetime
        for pws, pwe in possible_preferred_windows:
            current_intersection = (
                (pwe - pws)
                - max(pwe - window_end, timedelta())
                - max(window_start - pws, timedelta())
            )
            if current_intersection == intersection:
                closest_preferred_start = pws
                closest_preferred_end = pwe
                break
        else:
            raise Exception  # noqa: TRY002

        if intersection >= taskq.requested_duration:
            # There are 4 possible cases
            # W P P W
            # W P W P
            # P W W P
            # P W P W
            
            if window_start >= closest_preferred_start:
                # P W W P
                # P W P W
                starts_at = window_start
                ends_at = window_start + taskq.requested_duration
            else:
                # W P P W
                # W P W P
                starts_at = closest_preferred_start
                ends_at = closest_preferred_start + taskq.requested_duration

        elif intersection > timedelta():
            # There is some intersection smaller than requested duration
            # i.e two cases possible
            # P W P W
            # W P W P
            if closest_preferred_end <= window_end:
                starts_at = window_start
                ends_at = window_start + taskq.requested_duration
            else:
                starts_at = window_end - taskq.requested_duration
                ends_at = window_end
        elif closest_preferred_start >= window_end:
            # There is no intersection, and the preferred window is on the right of maintenance window
            # W W P P
            starts_at = window_end - taskq.requested_duration
            ends_at = window_end
        else:
            # There is no intersection, and the preferred window is on the left of maintenance window
            # P P W W
            starts_at = window_start
            ends_at = window_start + taskq.requested_duration

        return window_id, starts_at, ends_at
        

    @staticmethod
    def _insert_nopref(taskq: TaskQ[None], section_id: int) -> tuple[int, datetime, datetime]:
        payload = {
            "requested_duration": taskq.requested_duration,
            "priority": taskq.priority,
            "section_id": section_id,
        }

        res = cur.execute(
            """
            SELECT
                window_start,
                COALESCE(
                    (
                        SELECT task.starts_at FROM task
                        JOIN maintenance_window
                            ON task.maintenance_window_id = window_id
                        WHERE
                            task.priority >= :priority
                            AND task.starts_at >= window_start
                        ORDER BY
                            task.starts_at ASC
                        LIMIT 1
                    ),
                    m_window_end
                ) AS window_end,
                window_id
            FROM (
                SELECT
                    maintenance_window.starts_at AS window_start,
                    maintenance_window.ends_at AS m_window_end,
                    maintenance_window.id as window_id,
                    maintenance_window.section_id as section_id
                FROM maintenance_window
                UNION
                SELECT
                    task.ends_at AS window_start,
                    maintenance_window.ends_at AS m_window_end,
                    maintenance_window.id as window_id,
                    maintenance_window.section_id as section_id
                FROM task
                JOIN maintenance_window
                    ON maintenance_window.id = task.maintenance_window_id
                WHERE
                    task.priority >= :priority
            )
            WHERE
                section_id = :section_id
                AND window_start >= DATETIME('now', '+30 minutes')
                AND UNIXEPOCH(window_end) - UNIXEPOCH(window_start)
                    >= :requested_duration
            ORDER BY
                window_start ASC
            LIMIT
                1
            """,
            payload,
        )

        x: (
            tuple[
                str,
                str,
                int
            ]
            | None
        ) = res.fetchone()
        if x is None:
            raise Exception  # noqa: TRY002

        (
            starts_at,
            _ends_at,
            window_id
        ) = x

        return window_id, datetime.fromisoformat(starts_at), datetime.fromisoformat(starts_at) + taskq.requested_duration


    @staticmethod
    def insert_nopref(
        priority: int,
        section_id: int,
        requested_duration: timedelta
    ) -> list[Task]:
        queue: list[TaskQ] = [
            TaskQ[None](
                priority,
                requested_duration,
                None,
                None,
            ),
        ]

        heapify(queue)
        return Task._insert(queue, [], section_id)

    @classmethod
    def insert_pref(  # noqa: PLR0913, PLR0912, C901
        cls,
        preferred_starts_at: time,
        preferred_ends_at: time,
        priority: int,
        section_id: int,
        requested_duration: timedelta
    ) -> list[Task]:
        queue: list[TaskQ] = [
            TaskQ[time](
                priority,
                requested_duration,
                preferred_starts_at,
                preferred_ends_at,
            ),
        ]

        heapify(queue)
        return Task._insert(queue, [], section_id)
    

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
            preferred_starts_at,
            preferred_ends_at,
            requested_duration,
            priority,
            maintenance_window_id,
        ) = raw

        return cls(
            id,
            datetime.fromisoformat(starts_at),
            datetime.fromisoformat(ends_at),
            time.fromisoformat(preferred_starts_at) if preferred_starts_at is not None else None,
            time.fromisoformat(preferred_ends_at) if preferred_ends_at is not None else None,
            timedelta(seconds=requested_duration),
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
                preferred_starts_at TIME,
                preferred_ends_at TIME,
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
