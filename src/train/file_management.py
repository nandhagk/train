from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import time, timedelta
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Any

from torch import isin

from train.db import decode_time, timediff
from train.exceptions import InvalidFileDataError, UnsupportedFileTypeError, InvalidHeadersError, CriticalLogicError
from train.models.section import Section
from train.models.task import PartialTask, Task

if TYPE_CHECKING:
    from pathlib import Path
    from sqlite3 import Cursor

logger = logging.getLogger(__name__)


class FileManager(ABC):
    class Format(IntEnum):
        bare_minimum = auto()
        mas_recent = auto()

    @staticmethod
    def _get_time(raw: str) -> time | None:
        try:
            return decode_time(raw)
        except ValueError:
            return None
        
    @staticmethod
    def try_int(raw: str, default = 0):
        try:
            return int(raw)
        except ValueError:
            return default

    @staticmethod
    def get_manager(path: Path) -> type[FileManager]:
        if path.suffix == ".csv":
            return CSVManager

        if path.suffix == ".xlsx":
            return ExcelManager

        raise UnsupportedFileTypeError(path.suffix)

    def __init__(self, src: Path, dst: Path) -> None:
        self.src_path = src
        self.dst_path = dst

        self.headers: list[str]

        self.fmt: FileManager.Format | None  = None
    
    @staticmethod
    def get_file_fmt_type(headers: list[str]) -> Format:  # noqa: ARG004
        if "DATE" in headers:
            return FileManager.Format.mas_recent
        else:
            return FileManager.Format.bare_minimum
        
    def validate_headers(self):
        if self.fmt == FileManager.Format.bare_minimum:
            if not {
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
            }.issubset(self.headers):
                raise InvalidHeadersError(self.fmt, self.headers)
        
        elif self.fmt == FileManager.Format.mas_recent:
            if {
                "DATE",
                "Department",
                "DEN",
                "Block Section/ Yard",
                "CORRIDOR block section",
                # "corridor block period",
                "UP/ DN Line",
                # "Block demanded in Hrs(Day or Night)",
                "Demanded time (From)",
                "Demanded time (To)",
                "Block demanded in(MINS)",
                "Permitted time (From) No need to fill",
                "Permitted time (To) No need to fill",
                "BLOCK PERMITTED MINS",
                # "Location - FROM",
                # "Location - TO",
                "Nautre of work & Quantum of Output Planned",
                # "Need for disconnection (If Yes Track Circuit and Signals Affected) Please give specific details without fail",
                # "Caution required",
                # "Caution required (if yes with relaxation date dd:mm:yyyy)",
                # "Power Block & its Elementary Section. Please give specific details without fail",
                # "Resources needed (M/C, Manpower, Supervisors) Include Crane,JCB,porcelain or any other equipment also",
                # "Whether site preparation & resources ready",
                # "Supervisors to be deputed (JE/SSE with section)",
                # "Coaching repercussions/ Movement Repercussions",
                "Actual Block Granted From No need to fill",
                "Actual Block Granted To No need to fill",
                "Actual block duration MINS No need to fill",
                "Over all % granted for the day No need to fill",
                "Output as per Manual No need to fill",
                "Actual Output",
                "% Output vs Planned\nNo need to fill",
                # "% Output\nvs\nPlanned",
                # "PROGRESS",
                "LOCATION",
                "SECTION",
                "ARB/RB",
            }.issubset(self.headers):
                raise InvalidHeadersError(self.fmt, self.headers)

    def encode_tasks(self, cur: Cursor, tasks: list[Task]) -> list[dict]:
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
                TIME(task.ends_at),
                task.priority
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
            self.unmap(
                {
                    "priority"              : row[10],
                    "date"                  : row[0],
                    "block_section_or_yard" : (
                        f"{row[1].replace("_", " ")}"
                        if row[1] == row[2]
                        else f"{row[1]}-{row[2]}"
                    ),
                    "corridor_block"        : row[3],
                    "line"                  : row[4],
                    "demanded_time_from"    : row[5],
                    "demanded_time_to"      : row[6],
                    "block_demanded"        : row[7],
                    "permitted_time_from"   : row[8],
                    "permitted_time_to"     : row[9],
                    "block_permitted"       : row[7],
                }
            )
            for row in cur.fetchall()
        ]

        raise NotImplementedError

    def map(self, item: dict) -> dict[str, Any] | None:
        # TODO! Add additional information to taskq
        mapped: dict
        if self.fmt == FileManager.Format.bare_minimum:
            mapped = {"priority": 1} | item
        
        elif self.fmt == FileManager.Format.mas_recent:
            mapped = {
                "priority"              : 1,
                "date"                  : item["DATE"],
                "block_section_or_yard" : item["Block Section/ Yard"],
                "corridor_block"        : item["CORRIDOR block section"],
                "line"                  : item["UP/ DN Line"],
                "demanded_time_from"    : item["Demanded time (From)"],
                "demanded_time_to"      : item["Demanded time (To)"],
                "block_demanded"        : item["Block demanded in(MINS)"],
                "permitted_time_from"   : item["Permitted time (From) No need to fill"],
                "permitted_time_to"     : item["Permitted time (To) No need to fill"],
                "block_permitted"       : item["BLOCK PERMITTED MINS"]
            }
        
        else:
            raise CriticalLogicError("Format is None!")
        
        # Validate the type of data

        if not isinstance(mapped["priority"], int):
            logger.warn("Invalid priority")
            return None
        
        if not isinstance(mapped["block_section_or_yard"], str):
            logger.warn("Invalid section")
            return None

        if not isinstance(mapped["corridor_block"], str):
            logger.warn("Invalid block")
            return None
        
        if not isinstance(mapped["line"], str):
            logger.warn("Invalid line")
            return None
        
        mapped["demanded_time_from"] = FileManager._get_time(str(mapped["demanded_time_from"]))
        mapped["demanded_time_to"] = FileManager._get_time(str(mapped["demanded_time_to"]))
        
        mapped["block_demanded"] = FileManager.try_int(str(mapped["block_demanded"]), 0)
        
        return mapped
        
    def unmap(self, item: dict) -> dict:
        if self.fmt == FileManager.Format.bare_minimum:
            return item
        
        elif self.fmt == FileManager.Format.mas_recent:
            return {
                "DATE": item["date"],
                # "Department": item{"department"},
                # "DEN": item["DEN"],
                "Block Section/ Yard": item["block_section_or_yard"],
                "CORRIDOR block section": item["corridor_block"],
                # # "corridor block period",
                "UP/ DN Line": item["line"],
                # # "Block demanded in Hrs(Day or Night)",
                "Demanded time (From)": item["demanded_time_from"],
                "Demanded time (To)": item["demanded_time_to"],
                "Block demanded in(MINS)": item["block_demanded"],
                "Permitted time (From) No need to fill": item["permitted_time_from"],
                "Permitted time (To) No need to fill": item["permitted_time_to"],
                "BLOCK PERMITTED MINS": item["block_permitted"],
                # # "Location - FROM",
                # # "Location - TO",
                # "Nautre of work & Quantum of Output Planned": item["nature"],
                # # "Need for disconnection (If Yes Track Circuit and Signals Affected) Please give specific details without fail",
                # # "Caution required",
                # # "Caution required (if yes with relaxation date dd:mm:yyyy)",
                # # "Power Block & its Elementary Section. Please give specific details without fail",
                # # "Resources needed (M/C, Manpower, Supervisors) Include Crane,JCB,porcelain or any other equipment also",
                # # "Whether site preparation & resources ready",
                # # "Supervisors to be deputed (JE/SSE with section)",
                # # "Coaching repercussions/ Movement Repercussions",
                # "Actual Block Granted From No need to fill": item["actual_block_from"],
                # "Actual Block Granted To No need to fill": item["actual_block_to"],
                # "Actual block duration MINS No need to fill": item["block_actual"],
                # "Over all % granted for the day No need to fill": item["overall_per"],
                # "Output as per Manual No need to fill": item["output"],
                # "Actual Output",
                # "% Output vs Planned\nNo need to fill",
                # # "% Output\nvs\nPlanned",
                # # "PROGRESS",
                # "LOCATION",
                # "SECTION",
                # "ARB/RB",
            }
        
        else:
            raise CriticalLogicError("Format is None!")
        
    def decode(self, cur: Cursor, item: dict) -> PartialTask | None:
        mapped_item = self.map(item)
        if mapped_item is None:
            return None
        

        preferred_ends_at = mapped_item["demanded_time_to"]
        preferred_starts_at = mapped_item["demanded_time_from"]

        section = Section.find_by_name_and_line(
            cur,
            mapped_item["block_section_or_yard"],
            mapped_item["line"],
        )

        if section is None:
            logger.warning(
                "Could not find section: %s - %s",
                mapped_item["block_section_or_yard"],
                mapped_item["line"],
            )

            return None

        if preferred_starts_at is None or preferred_ends_at is None:
            if mapped_item["block_demanded"] != 0:
                return (
                    PartialTask(
                        int(mapped_item.get("priority", 1)),
                        timedelta(minutes=mapped_item["block_demanded"]),
                        preferred_starts_at,
                        preferred_ends_at,
                        section.id,
                    )
                )
            else:
                logger.warning("Invalid duration (It is empty)")
                return None

        assert preferred_starts_at is not None
        assert preferred_ends_at is not None

        if mapped_item["block_demanded"] != 0:
            return (
                PartialTask(
                    mapped_item["priority"],
                    timedelta(minutes=mapped_item["block_demanded"]),
                    preferred_starts_at,
                    preferred_ends_at,
                    section.id,
                )
            )
        else:
            return (
                PartialTask(
                    mapped_item["priority"],
                    timediff(preferred_starts_at, preferred_ends_at),
                    preferred_starts_at,
                    preferred_ends_at,
                    section.id,
                )
            )

        raise NotImplementedError

    @abstractmethod
    def read(
        self,
        cur: Cursor
    ) -> list[PartialTask]: ...

    @abstractmethod
    def write(self, cur: Cursor, tasks: list[Task]) -> None: ...


class CSVManager(FileManager):
    
    def read(
        self,
        cur: Cursor
    ) -> list[PartialTask]:
        import csv

        with self.src_path.open(newline="") as fd:
            reader = csv.DictReader(fd)
            data = [*reader]

        if not data:
            msg = "Please give file with data ;-;"
            raise InvalidFileDataError(msg)

        self.fmt = FileManager.get_file_fmt_type([*data[0].keys()])
        self.validate_headers()

        self.headers = [*data[0].keys()]

        taskqs = []
        for idx, item in enumerate(data):
            if (decoded := self.decode(cur, item)) is None:
                logger.warning(f"Ignoring item on row `{idx}` `{item}`")
                continue
            taskqs.append(decoded)

        return taskqs
        

    def write(
        self,
        cur: Cursor,
        tasks: list[Task]
    ) -> None:
        import csv

        data = self.encode_tasks(cur, tasks)

        with self.dst_path.open(mode="w", newline="") as fd:
            writer = csv.DictWriter(fd, self.headers)
            writer.writeheader()
            writer.writerows(data)


class ExcelManager(FileManager):
    def read(
        self,
        cur: Cursor
    ) -> list[PartialTask]:
        import openpyxl

        wb = openpyxl.load_workbook(self.src_path, read_only=True, data_only=True)
        sheet: openpyxl.worksheet.worksheet.Worksheet | None = wb.active  # type: ignore ()

        if sheet is None:
            msg = "Could not read excel sheet"
            raise InvalidFileDataError(msg)

        col_count = sheet.max_column

        self.headers = [str(sheet.cell(1, col).value) for col in range(1, col_count + 1)]
        
        self.fmt = FileManager.get_file_fmt_type(self.headers)
        self.validate_headers()

        data = []
        for row in sheet.iter_rows(min_row=2, min_col=1, max_col=col_count):
            if not row[0].value:
                continue

            data.append({self.headers[i]: row[i].value for i in range(col_count)})

        wb.close()
        taskqs = []
        for idx, item in enumerate(data):
            if (decoded := self.decode(cur, item)) is None:
                logger.warning(f"Ignoring item on row `{idx}` `{item}`")
                continue
            taskqs.append(decoded)

        return taskqs

    def write(
        self,
        cur: Cursor,
        tasks: list[Task]
    ) -> None:
        import openpyxl

        data = self.encode_tasks(cur, tasks)
        wb = openpyxl.Workbook(write_only=True)
        sheet = wb.create_sheet()

        sheet.append(self.headers)
        for row in data:
            sheet.append(list(row.get(heading, "") for heading in self.headers))

        wb.save(self.dst_path.as_posix())
        wb.close()
