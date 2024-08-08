from logging import getLogger
from pathlib import Path

from asyncpg import Connection, Record

from train.repositories.section import SectionRepository
from train.schemas.requested_task import CreateRequestedTask
from train.utils import timediff

from .formats.format import Format
from .formats.mas import MASFormat
from .handlers.excel import ExcelHandler
from .handlers.handler import Handler

logger = getLogger(__name__)


def get_file_handler(path: Path) -> type[Handler]:
    if path.suffix == ".xlsx":
        return ExcelHandler

    msg = f"Unexpected file extension `{path.suffix}`"
    raise RuntimeError(msg)


def get_file_format(_headers: list[str]) -> type[Format]:
    return MASFormat


class FileManager:
    def __init__(self, file: str) -> None:
        self.file = Path(file)
        self.handler = get_file_handler(self.file)

        self.headers, self._raw_data = self.handler.read_dict(self.file)
        self.format = get_file_format(self.headers)

    async def decode(self, con: Connection, item: dict) -> CreateRequestedTask:
        mapped_item = self.format.convert_to_standard(item)

        preferred_ends_at = mapped_item["demanded_time_to"]
        preferred_starts_at = mapped_item["demanded_time_from"]

        station_a, station_b = mapped_item["block_section_or_yard"].partition("-")[::2]

        section = await SectionRepository.find_one_by_line_and_names(
            con,
            station_a,
            station_b,
            mapped_item["line"],
        )

        if section is None:
            logger.warning(
                "Could not find section: %s - %s",
                mapped_item["block_section_or_yard"],
                mapped_item["line"],
            )

            msg = (
                "Invalid section"
                f' {mapped_item["block_section_or_yard"]}-{mapped_item["line"]}'
            )
            raise RuntimeError(msg)

        if mapped_item["block_demanded"] == 0 and (
            preferred_starts_at is None or preferred_ends_at is None
        ):
            # INSERT LOGGING
            msg = "Invalid duration (It is empty)"
            logger.warning(msg)
            raise RuntimeError(msg)

        if (preferred_starts_at is None) ^ (preferred_ends_at is None):
            # INSERT LOGGING
            msg = "Demanded range is not complete"
            logger.warning(msg)
            raise RuntimeError(msg)

        return CreateRequestedTask(
            priority=mapped_item["priority"],
            section_id=section.id,
            requested_duration=(
                mapped_item["block_demanded"]
                if mapped_item["block_demanded"] != 0
                else timediff(preferred_starts_at, preferred_ends_at)
            ),
            block=mapped_item["block_section_or_yard"],
            preferred_starts_at=preferred_starts_at,
            preferred_ends_at=preferred_ends_at,
            department=mapped_item["department"],
            den=mapped_item["den"],
            nature_of_work=mapped_item["nature_of_work"],
            location=mapped_item["location"],
            requested_date=mapped_item["date"],
        )

    async def get_tasks(self, con: Connection) -> list[CreateRequestedTask | None]:
        taskqs: list[CreateRequestedTask | None] = []
        for idx, item in enumerate(self._raw_data):
            try:
                decoded = await self.decode(con, item)
                taskqs.append(decoded)
            except Exception:  # noqa: PERF203
                # INSERT LOGGING
                logger.exception("WARNING: Ignoring item on row `%d` ", idx)
                taskqs.append(None)

        return taskqs

    async def encode_tasks(self, con: Connection, task_ids: list[int]) -> list[dict]:
        rows: list[Record] = await con.fetch(
            """
            SELECT
                slot.starts_at as requested_date,
                (
                    SELECT node.name FROM node
                    WHERE
                        node.id = section.from_id
                ),
                (
                    SELECT node.name FROM node
                    WHERE
                        node.id = section.to_id
                ),
                task.block,
                section.line,
                task.preferred_starts_at,
                task.preferred_ends_at,
                task.requested_duration,
                slot.starts_at,
                slot.ends_at,
                slot.priority,
                task.department,
                task.den,
                task.nature_of_work,
                task.location
            FROM task
            JOIN slot ON
                slot.task_id = task.id
            JOIN section ON
                section.id = slot.section_id
            WHERE
                task.id = any($1::int[])
            ORDER BY
                slot.starts_at ASC
            """,
            task_ids,
        )

        return [
            self.format.convert_from_standard(
                {
                    "priority": row["priority"],
                    "date": row["requested_date"].date(),
                    "block_section_or_yard": (
                        f"{row["from"].replace("_", " ")}"
                        if row["from"] == row["to"]
                        else f"{row["from"]}-{row["to"]}"
                    ),
                    "corridor_block": row["block"],
                    "line": row["line"],
                    "demanded_time_from": row["preferred_starts_at"],
                    "demanded_time_to": row["preferred_ends_at"],
                    "block_demanded": row["requested_duration"],
                    "permitted_time_from": row["starts_at"].time(),
                    "permitted_time_to": row["ends_at"].time(),
                    "block_permitted": row["requested_duration"],
                    "department": row["department"],
                    "den": row["den"],
                    "nature_of_work": row["nature_of_work"],
                    "location": row["location"],
                },
            )
            for row in rows
        ]

    async def write_tasks(self, con: Connection, tasks: list[int]) -> None:
        data = await self.encode_tasks(con, tasks)
        self.handler.write_dict(self.file, self.headers, data)
