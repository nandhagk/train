from collections.abc import Sequence
from typing import TypeAlias

from asyncpg import Connection
from msgspec import Struct

from train.models.task import PartialTask
from train.repositories.task import TaskRepository
from train.services.slot import NoFreeSlotError, SlotService, TaskSlotToInsert

InsertErr: TypeAlias = NoFreeSlotError


class TaskToInsert(PartialTask, frozen=True, kw_only=True):
    priority: int


class TaskInsertResult(Struct, frozen=True, kw_only=True):
    requested_tasks: list[int]
    good_tasks: list[int]
    bad_tasks: list[int]


class TaskService:
    @staticmethod
    async def insert_one(
        con: Connection,
        section_id: int,
        task: TaskToInsert,
    ) -> TaskInsertResult:
        return await TaskService.insert_many(con, section_id, [task])

    @staticmethod
    async def insert_many(
        con: Connection,
        section_id: int,
        tasks: Sequence[TaskToInsert],
    ) -> TaskInsertResult:
        created_tasks = await TaskRepository.insert_many(con, tasks)
        good_tasks, bad_tasks = await SlotService.insert_task_slots(
            con,
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
