from train.models.slot import Slot
from train.models.task import Task


class HydratedTask(Task, frozen=True, kw_only=True):
    priority: int
    section_id: int
    slots: list[Slot]
