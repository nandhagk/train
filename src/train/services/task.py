from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from train.models.task import PartialTask, Task
from train.services.slot import NoFreeSlotError, SlotService, TaskSlotToInsert

if TYPE_CHECKING:
    from sqlite3 import Cursor


InsertErr: TypeAlias = NoFreeSlotError


@dataclass(frozen=True)
class TaskToInsert(PartialTask):
    priority: int


@dataclass(frozen=True)
class TaskInsertResult:
    requested_tasks: list[int]
    good_tasks: list[int]
    bad_tasks: list[int]


class TaskService:
    @staticmethod
    def insert_one(
        cur: Cursor,
        section_id: int,
        task: TaskToInsert,
    ) -> TaskInsertResult:
        return TaskService.insert_many(cur, section_id, [task])

    @staticmethod
    def insert_many(
        cur: Cursor,
        section_id: int,
        tasks: list[TaskToInsert],
    ) -> TaskInsertResult:
        # TODO: migrate to postgres which allows RETURNING with bulk inserts
        created_tasks = [Task.insert_one(cur, task) for task in tasks]
        good_tasks, bad_tasks = SlotService.insert_task_slots(
            cur,
            section_id,
            [
                TaskSlotToInsert(
                    priority=task.priority,
                    preferred_starts_at=task.preferred_starts_at,
                    preferred_ends_at=task.preferred_ends_at,
                    requested_date=task.requested_date,
                    requested_duration=task.requested_duration,
                    task_id=created_task.id,
                )
                for task, created_task in zip(tasks, created_tasks)
            ],
        )

        return TaskInsertResult(
            requested_tasks=[created_task.id for created_task in created_tasks],
            good_tasks=good_tasks,
            bad_tasks=bad_tasks,
        )


# from __future__ import annotations

# from dataclasses import dataclass, field
# from datetime import UTC, datetime, time, timedelta
# from heapq import heapify, heappop, heappush
# from typing import TYPE_CHECKING, Generic, TypeAlias, TypeVar

# from result import Err, Ok, Result

# from train.db import decode_datetime, decode_timedelta, timediff, unixepoch, utcnow
# from train.exceptions import CriticalLogicError, NoFreeWindowError

# if TYPE_CHECKING:
#     from sqlite3 import Cursor, Row


# T = TypeVar("T", None, time)

# InsertOk: TypeAlias = tuple[int, datetime, datetime]
# InsertErr: TypeAlias = CriticalLogicError | NoFreeWindowError


# @dataclass(frozen=True)
# class PartialTask(Generic[T]):
#     priority: int
#     requested_duration: timedelta
#     preferred_starts_at: T
#     preferred_ends_at: T
#     section_id: int

#     department: str
#     den: str
#     nature_of_work: str
#     location: str

#     starts_at: datetime = field(default_factory=utcnow)

#     @property
#     def preferred_range(self) -> timedelta:
#         if self.preferred_starts_at is None or self.preferred_ends_at is None:
#             return timedelta(days=1)

#         return timediff(self.preferred_starts_at, self.preferred_ends_at)

#     def __lt__(self, other: PartialTask) -> bool:
#         """
#         Priority Order.

#         Priority (Hi)
#         -> Requested Duration (Hi)
#         -> Preferred Range (Lo)
#         -> Starts At (Lo)
#         """
#         if self.priority == other.priority:
#             if self.requested_duration == other.requested_duration:
#                 if self.preferred_range == other.preferred_range:
#                     return self.starts_at < other.starts_at
#                 return self.preferred_range < other.preferred_range
#             return self.requested_duration > other.requested_duration
#         return self.priority > other.priority


# @dataclass(frozen=True)
# class Task(Generic[T]):
#     id: int

#     department: str
#     den: str
#     nature_of_work: str
#     location: str

#     starts_at: datetime
#     ends_at: datetime

#     preferred_starts_at: T
#     preferred_ends_at: T
#     requested_duration: timedelta

#     priority: int

#     slot_id: int

#     @staticmethod
#     def insert_many(
#         cur: Cursor,
#         tasks: list[PartialTask],
#     ) -> Result[list[Task], InsertErr]:
#         heapify(tasks)

#         tasks_: list[Task] = []
#         while tasks:
#             task = heappop(tasks)
#             if task.preferred_ends_at is None or task.preferred_starts_at is None:
#                 res = Task._insert_nopref(cur, task)
#             else:
#                 res = Task._insert_pref(cur, task)

#             if isinstance(res, Err):
#                 cur.execute(
#                     f"""
#                     DELETE FROM task
#                     WHERE
#                         id IN ({', '.join(str(t.id) for t in tasks_)})
#                     """,
#                 )

#                 return res

#             window_id, starts_at, ends_at = res.value
#             payload = {
#                 "window_id": window_id,
#                 "starts_at": starts_at,
#                 "ends_at": ends_at,
#             }

#             cur.execute(
#                 """
#                 DELETE FROM task
#                 WHERE
#                     task.slot_id = :window_id
#                     AND (
#                         (task.starts_at > :starts_at AND task.starts_at < :ends_at)
#                         OR (task.ends_at > :starts_at AND task.ends_at < :ends_at)
#                         OR (:starts_at > task.starts_at AND :starts_at < task.ends_at)
#                         OR (task.starts_at = :starts_at AND task.ends_at <= :ends_at)
#                         OR (task.ends_at = :ends_at AND task.starts_at >= :starts_at)
#                     )
#                 RETURNING *
#                 """,
#                 payload,
#             )

#             for row in cur.fetchall():
#                 task_to_remove = Task.decode(row)
#                 heappush(
#                     tasks,
#                     PartialTask(
#                         priority=task_to_remove.priority,
#                         requested_duration=task_to_remove.requested_duration,
#                         preferred_starts_at=task_to_remove.preferred_starts_at,
#                         preferred_ends_at=task_to_remove.preferred_ends_at,
#                         section_id=task.section_id,
#                         department=task_to_remove.department,
#                         den=task_to_remove.den,
#                         nature_of_work=task_to_remove.nature_of_work,
#                         location=task_to_remove.location,
#                         starts_at=task_to_remove.starts_at,
#                     ),
#                 )

#             task_ = Task._insert(cur, task, starts_at, ends_at, window_id)
#             tasks_.append(task_)

#         return Ok(tasks_)

#     @staticmethod
#     def insert_one(
#         cur: Cursor,
#         taskq: PartialTask,
#     ) -> Result[list[Task], InsertErr]:
#         return Task.insert_many(cur, [taskq])

#     @staticmethod
#     def find_by_id(cur: Cursor, id: int) -> Task | None:
#         payload = {"id": id}

#         cur.execute(
#             """
#             SELECT task.* FROM task
#             WHERE
#                 task.id = :id
#             """,
#             payload,
#         )

#         row: Row | None = cur.fetchone()
#         if row is None:
#             return None

#         return Task.decode(row)

#     @staticmethod
#     def decode(row: Row) -> Task:
#         return Task(
#             id=row["id"],
#             department=row["department"],
#             den=row["den"],
#             nature_of_work=row["nature_of_work"],
#             location=row["location"],
#             starts_at=row["starts_at"],
#             ends_at=row["ends_at"],
#             preferred_starts_at=row["preferred_starts_at"],
#             preferred_ends_at=row["preferred_ends_at"],
#             requested_duration=decode_timedelta(row["requested_duration"]),
#             priority=row["priority"],
#             slot_id=row["slot_id"],
#         )

#     @staticmethod
#     def _insert(
#         cur: Cursor,
#         taskq: PartialTask,
#         starts_at: datetime,
#         ends_at: datetime,
#         window_id: int,
#     ) -> Task:
#         payload = {
#             "department": taskq.department,
#             "den": taskq.den,
#             "nature_of_work": taskq.nature_of_work,
#             "location": taskq.location,
#             "starts_at": starts_at,
#             "ends_at": ends_at,
#             "preferred_starts_at": taskq.preferred_starts_at,
#             "preferred_ends_at": taskq.preferred_ends_at,
#             "requested_duration": taskq.requested_duration,
#             "priority": taskq.priority,
#             "slot_id": window_id,
#         }

#         cur.execute(
#             """
#             INSERT INTO task (
#                 department,
#                 den,
#                 nature_of_work,
#                 location,
#                 starts_at,
#                 ends_at,
#                 preferred_starts_at,
#                 preferred_ends_at,
#                 requested_duration,
#                 priority,
#                 slot_id
#             ) VALUES (
#                 :department,
#                 :den,
#                 :nature_of_work,
#                 :location,
#                 :starts_at,
#                 :ends_at,
#                 :preferred_starts_at,
#                 :preferred_ends_at,
#                 :requested_duration,
#                 :priority,
#                 :slot_id
#             ) RETURNING *
#             """,
#             payload,
#         )

#         task = Task.decode(cur.fetchone())
#         assert task is not None

#         return task

#     @staticmethod
#     def _insert_pref(
#         cur: Cursor,
#         taskq: PartialTask[time],
#     ) -> Result[InsertOk, InsertErr]:
#         payload = {
#             "requested_duration": taskq.requested_duration,
#             "priority": taskq.priority,
#             "section_id": taskq.section_id,
#         }

#         cur.execute(
#             """
#             SELECT
#                 window_start,
#                 COALESCE(
#                     (
#                         SELECT MIN(task.starts_at) FROM task
#                         WHERE
#                             task.priority >= :priority
#                             AND task.starts_at >= window_start
#                             AND task.slot_id = window_id
#                     ),
#                     m_window_end
#                 ) AS window_end,
#                 window_id
#             FROM (
#                 SELECT
#                     slot.starts_at AS window_start,
#                     slot.ends_at AS m_window_end,
#                     slot.id AS window_id,
#                     slot.section_id AS section_id
#                 FROM slot
#                 UNION
#                 SELECT
#                     task.ends_at AS window_start,
#                     slot.ends_at AS m_window_end,
#                     slot.id AS window_id,
#                     slot.section_id AS section_id
#                 FROM task
#                 JOIN slot
#                     ON slot.id = task.slot_id
#                 WHERE
#                     task.priority >= :priority
#             )
#             WHERE
#                 section_id = :section_id
#                 AND window_start >= DATETIME('now', '+1 day')
#                 AND UNIXEPOCH(window_end) - UNIXEPOCH(window_start)
#                     >= :requested_duration
#             """,
#             payload,
#         )

#         p_starts = unixepoch(taskq.preferred_starts_at)
#         p_ends = unixepoch(taskq.preferred_ends_at)
#         if p_ends <= p_starts:
#             p_starts -= timedelta(days=1)

#         def mapper(row: Row) -> tuple[timedelta, datetime, datetime, int]:
#             window_start = row["window_start"]
#             window_end = decode_datetime(row["window_end"])
#             window_id = row["window_id"]

#             m_starts = unixepoch(window_start.time())
#             m_ends = unixepoch(window_end.time())
#             if m_ends <= m_starts:
#                 m_starts -= timedelta(days=1)

#             intersection = max(
#                 (p_ends - p_starts)
#                 - max(p_ends - m_ends, timedelta())
#                 - max(m_starts - p_starts, timedelta()),
#                 (p_ends - p_starts)
#                 - max(p_ends - m_ends + timedelta(days=1), timedelta())
#                 - max(m_starts - p_starts - timedelta(days=1), timedelta()),
#                 (p_ends - p_starts)
#                 - max(p_ends - m_ends - timedelta(days=1), timedelta())
#                 - max(m_starts - p_starts + timedelta(days=1), timedelta()),
#             )

#             return intersection, window_start, window_end, window_id

#         data = [mapper(row) for row in cur.fetchall()]
#         if len(data) == 0:
#             return Err(NoFreeWindowError(taskq))

#         intersection, window_start, window_end, window_id = max(
#             data,
#             key=lambda z: (min(z[0], taskq.requested_duration), utcnow() - z[1]),
#         )

#         possible_preferred_dates = (
#             window_start - timedelta(days=1),
#             window_start,
#             window_end,
#             window_end + timedelta(days=1),
#         )

#         possible_preferred_windows = (
#             (
#                 possible_preferred_date.combine(
#                     possible_preferred_date.date(),
#                     taskq.preferred_starts_at,
#                     UTC,
#                 ),
#                 possible_preferred_date.combine(
#                     possible_preferred_date.date(),
#                     taskq.preferred_ends_at,
#                     UTC,
#                 )
#                 + timedelta(
#                     days=int(taskq.preferred_ends_at <= taskq.preferred_starts_at),
#                 ),
#             )
#             for possible_preferred_date in possible_preferred_dates
#         )

#         closest_preferred_start: datetime
#         closest_preferred_end: datetime
#         for pws, pwe in possible_preferred_windows:
#             current_intersection = (
#                 (pwe - pws)
#                 - max(pwe - window_end, timedelta())
#                 - max(window_start - pws, timedelta())
#             )
#             if current_intersection == intersection:
#                 closest_preferred_start = pws
#                 closest_preferred_end = pwe
#                 break
#         else:
#             msg = "Could not find window that gave max intersection"
#             return Err(CriticalLogicError(msg))

#         if intersection >= taskq.requested_duration:
#             # There are 4 possible cases
#             # W P P W
#             # W P W P
#             # P W W P
#             # P W P W
#             if window_start >= closest_preferred_start:
#                 # P W W P
#                 # P W P W
#                 starts_at = window_start
#                 ends_at = window_start + taskq.requested_duration
#             else:
#                 # W P P W
#                 # W P W P
#                 starts_at = closest_preferred_start
#                 ends_at = closest_preferred_start + taskq.requested_duration
#         elif intersection > timedelta():
#             # There is some intersection smaller than requested duration
#             # i.e two cases possible
#             # P W P W
#             # W P W P
#             if closest_preferred_end <= window_end:
#                 starts_at = window_start
#                 ends_at = window_start + taskq.requested_duration
#             else:
#                 starts_at = window_end - taskq.requested_duration
#                 ends_at = window_end
#         elif closest_preferred_start >= window_end:
#             # There is no intersection, and the preferred window
#             # is on the right of maintenance window
#             # W W P P
#             starts_at = window_end - taskq.requested_duration
#             ends_at = window_end
#         else:
#             # There is no intersection, and the preferred window
#             # is on the left of maintenance window
#             # P P W W
#             starts_at = window_start
#             ends_at = window_start + taskq.requested_duration

#         return Ok((window_id, starts_at, ends_at))

#     @staticmethod
#     def _insert_nopref(
#         cur: Cursor,
#         taskq: PartialTask[None],
#     ) -> Result[InsertOk, InsertErr]:
#         payload = {
#             "requested_duration": taskq.requested_duration,
#             "priority": taskq.priority,
#             "section_id": taskq.section_id,
#         }

#         cur.execute(
#             """
#             SELECT
#                 window_start,
#                 COALESCE(
#                     (
#                         SELECT MIN(task.starts_at) FROM task
#                         WHERE
#                             task.priority >= :priority
#                             AND task.starts_at >= window_start
#                             AND task.slot_id = window_id
#                     ),
#                     m_window_end
#                 ) AS window_end,
#                 window_id
#             FROM (
#                 SELECT
#                     slot.starts_at AS window_start,
#                     slot.ends_at AS m_window_end,
#                     slot.id AS window_id,
#                     slot.section_id AS section_id
#                 FROM slot
#                 UNION
#                 SELECT
#                     task.ends_at AS window_start,
#                     slot.ends_at AS m_window_end,
#                     slot.id AS window_id,
#                     slot.section_id AS section_id
#                 FROM task
#                 JOIN slot
#                     ON slot.id = task.slot_id
#                 WHERE
#                     task.priority >= :priority
#             )
#             WHERE
#                 section_id = :section_id
#                 AND window_start >= DATETIME('now', '+1 day')
#                 AND UNIXEPOCH(window_end) - UNIXEPOCH(window_start)
#                     >= :requested_duration
#             ORDER BY
#                 window_start ASC
#             LIMIT
#                 1
#             """,
#             payload,
#         )

#         row: Row | None = cur.fetchone()
#         if row is None:
#             return Err(NoFreeWindowError(taskq))

#         window_start = row["window_start"]
#         window_id = row["window_id"]

#         starts_at = window_start
#         ends_at = starts_at + taskq.requested_duration

#         return Ok((window_id, starts_at, ends_at))
