from train.models.task import PartialTask, Task


class CreateRequestedTask(PartialTask, frozen=True, kw_only=True):
    priority: int
    section_id: int


class UpdateRequestedTask(Task, frozen=True, kw_only=True):
    priority: int
    section_id: int


class HydratedRequestedTask(Task, frozen=True, kw_only=True):
    priority: int
    section_id: int
