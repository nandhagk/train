from collections import defaultdict
from typing import TYPE_CHECKING

from asyncpg import Connection

from train.repositories.requested_task import RequestedTaskRepository
from train.services.task import TaskService

if TYPE_CHECKING:
    from train.models.requested_task import RequestedTask


class RequestedTaskService:
    @staticmethod
    async def schedule_many(con: Connection, ids: list[int]) -> None:
        tasks = await RequestedTaskRepository.find_many_by_ids(con, ids)

        task_map: defaultdict[int, list[RequestedTask]] = defaultdict(list)
        for task in tasks:
            task_map[task.section_id].append(task)

        for section_id, task in task_map.items():
            await TaskService.insert_many(con, section_id, task)  # type: ignore ()
