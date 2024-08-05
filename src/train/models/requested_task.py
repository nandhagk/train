from train.models.task import PartialTask, Task


class PartialRequestedTask(PartialTask, frozen=True, kw_only=True):
    priority: int
    section_id: int


class RequestedTask(Task, frozen=True, kw_only=True):
    priority: int
    section_id: int
