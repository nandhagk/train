from collections import defaultdict
from collections.abc import Iterable

from asyncpg import Connection

from train.models.requested_task import RequestedTask
from train.repositories.requested_task import RequestedTaskRepository
from train.repositories.task import TaskRepository
from train.schemas.requested_task import (
    CreateRequestedTask,
    HydratedRequestedTask,
    UpdateRequestedTask,
)
from train.services.slot import SlotService, TaskSlotToInsert


class RequestedTaskService:
    @staticmethod
    async def insert_one(
        con: Connection,
        requested_task: CreateRequestedTask,
    ) -> HydratedRequestedTask:
        task = await TaskRepository.insert_one(con, requested_task)
        return await RequestedTaskRepository.insert_one(
            con,
            RequestedTask(
                id=task.id,
                priority=requested_task.priority,
                section_id=requested_task.section_id,
            ),
        )

    @staticmethod
    async def update_one(
        con: Connection,
        requested_task: UpdateRequestedTask,
    ) -> HydratedRequestedTask | None:
        await TaskRepository.update_one(con, requested_task)
        return await RequestedTaskRepository.update_one(
            con,
            RequestedTask(
                id=requested_task.id,
                priority=requested_task.priority,
                section_id=requested_task.section_id,
            ),
        )

    @staticmethod
    async def schedule_many(con: Connection, ids: list[int]) -> None:
        requested_tasks = await RequestedTaskRepository.find_many_by_ids(con, ids)

        task_map: defaultdict[int, list[HydratedRequestedTask]] = defaultdict(list)
        for task in requested_tasks:
            task_map[task.section_id].append(task)

        for section_id, tasks in task_map.items():
            await RequestedTaskService.schedule_many_by_section(con, section_id, tasks)

    @staticmethod
    async def schedule_many_by_section(
        con: Connection,
        section_id: int,
        tasks: Iterable[HydratedRequestedTask],
    ) -> tuple[list[int], list[int]]:
        return await SlotService.insert_task_slots(
            con,
            section_id,
            [
                TaskSlotToInsert(
                    priority=task.priority,
                    preferred_starts_at=task.preferred_starts_at,
                    preferred_ends_at=task.preferred_ends_at,
                    requested_date=task.requested_date,
                    requested_duration=task.requested_duration,
                    task_id=task.id,
                )
                for task in tasks
            ],
        )
