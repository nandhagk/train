from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import time, timedelta
from enum import IntEnum, auto
from typing import TYPE_CHECKING

from train.db import decode_time
from train.models.section import Section
from train.models.task import PartialTask, Task

if TYPE_CHECKING:
    from pathlib import Path
    from sqlite3 import Cursor

logger = logging.getLogger(__name__)


class FileManager(ABC):
    @staticmethod
    def _get_time(raw: str) -> time | None:
        try:
            return decode_time(raw)
        except ValueError:
            return None

    class Format(IntEnum):
        bare_minimum = auto()

    @staticmethod
    def get_file_fmt_type(header: list[str]) -> Format:  # noqa: ARG004
        return FileManager.Format.bare_minimum

    @staticmethod
    def get_headers(fmt: Format) -> list[str]:
        if fmt == FileManager.Format.bare_minimum:
            return [
                "date",
                "block_section_or_yard",
                "corridor_block",
                "line",
                "demanded_time_from",
                "demanded_time_to",
                "block_demanded",
                "permitted_time_from",
                "permitted_time_to",
                "block_permitted",
            ]

        return []

    @staticmethod
    def encode_tasks(cur: Cursor, tasks: list[Task], fmt: Format) -> list[dict]:

        if fmt == FileManager.Format.bare_minimum:
            cur.execute(
                f"""
                SELECT
                    DATE(task.starts_at),
                    (
                        SELECT station.name FROM station
                        WHERE
                            station.id = section.from_id
                    ),
                    (
                        SELECT station.name FROM station
                        WHERE
                            station.id = section.to_id
                    ),
                    block.name,
                    section.line,
                    task.preferred_starts_at,
                    task.preferred_ends_at,
                    task.requested_duration / 60,
                    TIME(task.starts_at),
                    TIME(task.ends_at)
                FROM task
                JOIN maintenance_window ON
                    maintenance_window.id = task.maintenance_window_id
                JOIN section ON
                    section.id = maintenance_window.section_id
                JOIN station ON
                    station.id = section.from_id
                JOIN block ON
                    block.id = station.block_id
                WHERE task.id IN ({', '.join(str(task.id) for task in tasks)})
                ORDER BY
                    task.starts_at ASC
                """,  # noqa: S608
            )

            return [
                {
                    "date": row[0],
                    "block_section_or_yard": (
                        f"{row[1].replace("_", " ")}"
                        if row[1] == row[2]
                        else f"{row[1]}-{row[2]}"
                    ),
                    "corridor_block": row[3],
                    "line": row[4],
                    "demanded_time_from": row[5],
                    "demanded_time_to": row[6],
                    "block_demanded": row[7],
                    "permitted_time_from": row[8],
                    "permitted_time_to": row[9],
                    "block_permitted": row[7],
                }
                for row in cur.fetchall()
            ]

        return {}

    @staticmethod
    def get_manager(path: Path) -> type[FileManager]:
        if path.suffix == ".csv":
            return CSVManager

        if path.suffix == ".xlsx":
            return ExcelManager

        msg = f"Unsupported file extension `{path.suffix}`"
        raise Exception(msg)

    @staticmethod
    def decode(cur: Cursor, item: dict, fmt: Format) -> PartialTask | None:
        if fmt == FileManager.Format.bare_minimum:
            preferred_ends_at = FileManager._get_time(str(item["demanded_time_to"]))
            preferred_starts_at = FileManager._get_time(
                str(item["demanded_time_from"]),
            )

            section = Section.find_by_name_and_line(
                cur,
                item["section_name"],
                item["line"],
            )

            if section is None:
                logger.warning(
                    "Could not find section: %s - %s",
                    item["section_name"],
                    item["line"],
                )

                return None

            if preferred_starts_at is None or preferred_ends_at is None:
                return PartialTask(
                    int(item.get("priority", 1)),
                    timedelta(minutes=int(item["duration"])),
                    preferred_starts_at,
                    preferred_ends_at,
                    section.id,
                )

            assert preferred_starts_at is not None
            assert preferred_ends_at is not None

            return PartialTask(
                int(item.get("priority", 1)),
                timedelta(minutes=int(item["duration"])),
                preferred_starts_at,
                preferred_ends_at,
                section.id,
            )

        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def read(
        cur: Cursor,
        path: Path,
        fmt: Format | None = None,
    ) -> tuple[Format, list[PartialTask]]: ...

    @staticmethod
    @abstractmethod
    def write(cur: Cursor, path: Path, tasks: list[Task], fmt: Format) -> None: ...


class CSVManager(FileManager):
    @staticmethod
    def read(
        cur: Cursor,
        path: Path,
        fmt: FileManager.Format | None = None,
    ) -> tuple[FileManager.Format, list[PartialTask]]:
        import csv

        with path.open(newline="") as fd:
            reader = csv.DictReader(fd)
            data = [*reader]

        if not data:
            msg = "Please give file with data ;-;"
            raise Exception(msg)

        if fmt is None:
            fmt = FileManager.get_file_fmt_type([*data[0].keys()])

        return (
            fmt,
            list(filter(None, [FileManager.decode(cur, item, fmt) for item in data])),
        )

    @staticmethod
    def write(
        cur: Cursor,
        path: Path,
        tasks: list[Task],
        fmt: FileManager.Format,
    ) -> None:
        import csv

        data = FileManager.encode_tasks(cur, tasks, fmt)

        with path.open(mode="w", newline="") as fd:
            writer = csv.DictWriter(fd, FileManager.get_headers(fmt))
            writer.writeheader()
            writer.writerows(data)


class ExcelManager(FileManager):
    @staticmethod
    def read(
        cur: Cursor,
        path: Path,
        fmt: FileManager.Format | None = None,
    ) -> tuple[FileManager.Format, list[PartialTask]]:
        import openpyxl

        wb = openpyxl.load_workbook(path, read_only=True)
        sheet: openpyxl.worksheet.worksheet.Worksheet | None = wb.active  # type: ignore ()

        if sheet is None:
            msg = "Could not read excel sheet"
            raise Exception(msg)

        col_count = sheet.max_column

        headers = [str(sheet.cell(1, col).value) for col in range(1, col_count + 1)]
        if fmt is None:
            fmt = FileManager.get_file_fmt_type(headers)

        data = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=col_count):
            if not row[0].value:
                break

            data.append({headers[i]: row[i].value for i in range(col_count)})

        wb.close()
        return (
            fmt,
            list(filter(None, [FileManager.decode(cur, item, fmt) for item in data])),
        )

    @staticmethod
    def write(
        cur: Cursor,
        path: Path,
        tasks: list[Task],
        fmt: FileManager.Format,
    ) -> None:
        import openpyxl

        data = FileManager.encode_tasks(cur, tasks, fmt)
        wb = openpyxl.Workbook(write_only=True)
        sheet = wb.create_sheet()

        headers = FileManager.get_headers(fmt)

        sheet.append(headers)
        for row in data:
            sheet.append(list(row.values()))

        wb.save(path.as_posix())
        wb.close()
