from src.train.models.slot import Slot
from src.train.models.task import Task


class HydratedTask(Task, frozen=True, kw_only=True):
    priority: int
    section_id: int
    slots: list[Slot]
