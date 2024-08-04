from datetime import datetime, time, timedelta
from pathlib import Path
from sqlite3 import Cursor
from typing import Any, cast

from train.file_management.formats.format import Standard
from .handlers import Handler, ExcelHandler
from .formats import Format, MASFormat
from train.db import decode_date, decode_time, timediff
from train.models.section import Section
from train.services.task import TaskToInsert

def get_file_handler(path: Path) -> type[Handler]:
    if path.suffix == ".xlsx":
        return ExcelHandler
    
    raise RuntimeError(f"Unexpected file extension `{path.suffix}`")

def get_file_format(headers: list[str]) -> type[Format]:
    return MASFormat

class FileManager:
    def __init__(self, file: str) -> None:
        self.file = Path(file)
        self.handler = get_file_handler(self.file)

        self.headers, self._raw_data = self.handler.read_dict(self.file)
        self.format = get_file_format(self.headers)

    def decode(self, cur: Cursor, item: dict) -> tuple[TaskToInsert, int]:
        mapped_item = self.format.convert_to_standard(item)
       
        preferred_ends_at = mapped_item["demanded_time_to"]
        preferred_starts_at = mapped_item["demanded_time_from"]

        station_a, station_b = mapped_item["block_section_or_yard"].partition("-")[::2]

        section = Section.find_by_node_name(
            cur,
            station_a, station_b,
            mapped_item["line"],
        )

        if section is None:
            # INSERT LOGGING
            print(
                "Could not find section: %s - %s",
                mapped_item["block_section_or_yard"],
                mapped_item["line"],
            )

            raise RuntimeError(
                "Invalid section"
                f' {mapped_item["block_section_or_yard"]}-{mapped_item["line"]}',
            )

        if mapped_item["block_demanded"] == 0 and (
            preferred_starts_at is None or preferred_ends_at is None
        ):
            # INSERT LOGGING
            print("Invalid duration (It is empty)")
            raise RuntimeError("Invalid duration (It is empty)")

        if (preferred_starts_at is None) ^ (preferred_ends_at is None):
            # INSERT LOGGING
            print("Demanded range is not complete")
            raise RuntimeError("Demanded range is not complete")

        return (
            TaskToInsert(
                priority=mapped_item["priority"],
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
                requested_date=mapped_item["date"] 
            ), section.id
        )

    def get_tasks(self, cur: Cursor) -> list[tuple[TaskToInsert, int] | None]:
        taskqs: list[tuple[TaskToInsert, int] | None] = []
        for idx, item in enumerate(self._raw_data):
            try:
                decoded = self.decode(cur, item)
                taskqs.append(decoded)
            except Exception as e:
                # INSERT LOGGING
                print("WARNING: Ignoring item on row `%d` ", idx)
                print(e)
                taskqs.append(None)

        return taskqs   

    def encode_tasks(self, cur: Cursor, tasks: list[int]) -> list[dict]:
        cur.execute(
            f"""
            SELECT
                DATE(slot.starts_at),
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
                task.requested_duration / 60,
                TIME(slot.starts_at),
                TIME(slot.ends_at),
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
                task.id IN ({', '.join(map(str, tasks))})
            ORDER BY
                slot.starts_at ASC
            """,  # noqa: S608
        )

        return  [
            self.format.convert_from_standard(
                ( {
                    "priority": row[10],
                    "date": decode_date(row[0]),
                    "block_section_or_yard": (
                        f"{row[1].replace("_", " ")}"
                        if row[1] == row[2]
                        else f"{row[1]}-{row[2]}"
                    ),
                    "corridor_block": row[3],
                    "line": row[4],
                    "demanded_time_from": decode_time(row[5]),
                    "demanded_time_to": decode_time(row[6]),
                    "block_demanded": timedelta(minutes=int(row[7])),
                    "permitted_time_from": time.fromisoformat(row[8]),
                    "permitted_time_to": time.fromisoformat(row[9]),
                    "block_permitted": timedelta(minutes=int(row[7])),
                    "department": row[11],
                    "den": row[12],
                    "nature_of_work": row[13],
                    "location": row[14],
                }),
            )
            for row in cur.fetchall()
        ]

    def write_tasks(self, cur: Cursor, tasks: list[int]) -> None:
        data = self.encode_tasks(cur, tasks)
        self.handler.write_dict(self.file, self.headers, data)
