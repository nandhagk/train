from typing import ClassVar, TypeVar

from asyncpg import Pool
from blacksheep import Application, Content, Request, Response, delete, get, post, put
from blacksheep.server.bindings import Binder, BoundValue
from msgspec import Struct, ValidationError
from msgspec.json import Decoder

from train.repositories.requested_task import RequestedTaskRepository
from train.schemas.requested_task import CreateRequestedTask, UpdateRequestedTask
from train.services.requested_task import RequestedTaskService
from train.utils import ENCODER, pool_factory

T = TypeVar("T")


class FromJSON(BoundValue[T]):
    decoders: ClassVar[dict[type, Decoder]] = {}

    def __class_getitem__(cls, struct: type) -> object:
        if struct not in cls.decoders:
            cls.decoders[struct] = Decoder(type=struct)

        return super().__class_getitem__(struct)  # type: ignore ()


class JSONBinder(Binder):
    handle: ClassVar[type[FromJSON]] = FromJSON

    async def get_value(self, request: Request):
        data = await request.read()
        assert data is not None

        return self.handle.decoders[self.expected_type].decode(data)


def json(data: object, status: int = 200) -> Response:
    """Return json response."""
    return Response(
        status,
        content=Content(b"application/json", ENCODER.encode(data)),
    )


app = Application()


@app.lifespan
async def register_pool(app: Application):
    async with pool_factory() as pool:
        app.services.register(Pool, instance=pool)
        yield


@app.exception_handler(ValidationError)
async def validation_error_handler(
    _app: Application,
    _request: Request,
    exc: ValidationError,
):
    return json({"error": str(exc)}, 400)


class HealthStatus(Struct):
    status: str


@get("/api/health")
async def health() -> Response:
    return json(HealthStatus(status="UP"))


@get("/api/requested_task")
async def find_all_requested_tasks(pool: Pool) -> Response:
    async with pool.acquire() as con, con.transaction():
        tasks = await RequestedTaskRepository.find_all(con)

    return json(tasks)


@get("/api/requested_task/{id}")
async def find_requested_task_by_id(pool: Pool, id: int) -> Response:
    async with pool.acquire() as con, con.transaction():
        task = await RequestedTaskRepository.find_one_by_id(con, id)

    return json(task)


@post("/api/requested_task")
async def created_requested_task(
    pool: Pool,
    data: FromJSON[CreateRequestedTask],
) -> Response:
    task = data.value
    async with pool.acquire() as con, con.transaction():
        task = await RequestedTaskService.insert_one(con, task)

    return json(task, status=201)


@put("/api/requested_task")
async def update_requested_task(
    pool: Pool,
    data: FromJSON[UpdateRequestedTask],
) -> Response:
    task = data.value
    async with pool.acquire() as con, con.transaction():
        task = await RequestedTaskService.update_one(con, task)

    return json(task)


@delete("/api/requested_task/{id}")
async def remove_requested_task(pool: Pool, id: int) -> Response:
    async with pool.acquire() as con, con.transaction():
        task = await RequestedTaskRepository.delete_one_by_id(con, id)

    return json(task)


@post("/api/requested_task/schedule")
async def schedule_requested_tasks(pool: Pool, data: FromJSON[list[int]]) -> Response:
    """Schedule list of tasks by their ids."""
    ids = data.value
    async with pool.acquire() as con, con.transaction():
        await RequestedTaskService.schedule_many(con, ids)

    return json({"success": True}, status=201)
