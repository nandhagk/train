from abc import abstractmethod, ABC

from train.models.task import TaskQ, Task
from train.models.section import Section
from enum import IntEnum, auto
from datetime import time, datetime, timedelta
from train.db import cur


class FileManager(ABC):
    @staticmethod
    def _get_time(raw: str) -> time | None:
        for fmt in [
            "%H:%M", "%H:%M:%S"
        ]:
            try:
                return datetime.strptime(
                    str(raw),
                    fmt,
                ).time()
            
            except ValueError:
                continue
        return None

    class Format(IntEnum):
        bare_minimum = auto()

    @staticmethod
    def get_file_fmt_type(header: list[str]) -> Format:
        return FileManager.Format.bare_minimum
    
    @staticmethod
    def get_headers(fmt: Format):
        if fmt == FileManager.Format.bare_minimum:
            return ["date",
                    # "department",
                    "block_section_or_yard",
                    "corridor_block",
                    "line",
                    "demanded_time_from",
                    "demanded_time_to",
                    "block_demanded",
                    "permitted_time_from",
                    "permitted_time_to",
                    "block_permitted"]

    @staticmethod
    def encode_tasks(tasks: list[Task], fmt: Format):
        if fmt == FileManager.Format.bare_minimum:
            cur.execute(
                f"""
                SELECT
                    DATE(task.starts_at),
                    (SELECT station.name FROM station WHERE station.id = section.from_id),
                    (SELECT station.name FROM station WHERE station.id = section.to_id),
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
                WHERE task.id in ({' '.join(str(task.id) for task in tasks)})
                ORDER BY
                    task.starts_at ASC
                """
            )
            return [
                {
                    "date": x[0],
                    # "department": "ENGG",
                    "block_section_or_yard": (
                        f"{x[1].replace("_", " ")}" if x[1] == x[2] else f"{x[1]}-{x[2]}"
                    ),
                    "corridor_block": x[3],
                    "line": x[4],
                    "demanded_time_from": x[5],
                    "demanded_time_to": x[6],
                    "block_demanded": x[7],
                    "permitted_time_from": x[8],
                    "permitted_time_to": x[9],
                    "block_permitted": x[7],
                }
                for x in cur.fetchall()
            ]
        
    @staticmethod
    def get_manager(path: str) -> type['FileManager']:
        if path.endswith(".csv"): return CSVManager
        elif path.endswith(".xlsx"): return ExcelManager

        raise Exception(f"Unsupported file extension `{path.split(".")[-1]}`")

    @staticmethod
    def decode(item: dict, fmt: Format):
        if fmt == FileManager.Format.bare_minimum:
            preferred_ends_at = FileManager._get_time(item['demanded_time_to'])
            preferred_starts_at = FileManager._get_time(item['demanded_time_from'])

            section = Section.find_by_name_and_line(item['section_name'], item['line'])
            if section is None:
                raise Exception(f"Invalid section `{item['section_name'], item['line']}`")

            if preferred_starts_at is None and preferred_ends_at is None:
                return TaskQ[None](
                    priority=int(item['priority']),
                    preferred_ends_at = preferred_ends_at,
                    preferred_starts_at = preferred_starts_at,
                    requested_duration = timedelta(minutes = int(item['duration']))              
                ), section.id
            else:
                assert preferred_starts_at is not None and preferred_ends_at is not None
                return TaskQ[time](
                    priority=int(item['priority']),
                    preferred_ends_at = preferred_ends_at,
                    preferred_starts_at = preferred_starts_at,
                    requested_duration = timedelta(minutes = int(item['duration']))     
                ), section.id
        else:
            raise NotImplementedError

    @staticmethod
    @abstractmethod
    def read(path: str, fmt: Format | None = None) -> tuple[Format, list[tuple[TaskQ, int]]]:...

    @staticmethod
    @abstractmethod
    def write(path: str, tasks: list[Task], fmt: Format):
        pass
    
class CSVManager(FileManager):
    @staticmethod
    def read(path: str, fmt: FileManager.Format | None = None) -> tuple[FileManager.Format, list[tuple[TaskQ, int]]]:
        import csv
        with open(path) as fd:
            reader = csv.DictReader(fd)
            data = [*reader]

        if not data:
            raise Exception("Please give file with data ;-;")

        if fmt is None:
            fmt = FileManager.get_file_fmt_type([*data[0].keys()])

        return fmt, [
            FileManager.decode(item, fmt) for item in data
        ]
    
    @staticmethod
    def write(path: str, tasks: list[Task], fmt: FileManager.Format):
        import csv
        data = FileManager.encode_tasks(tasks, fmt)

        with open(path) as fd:
            writer = csv.DictWriter(fd, FileManager.get_headers(fmt))
            writer.writerows(data)

class ExcelManager(FileManager):
    @staticmethod
    def read(path: str, fmt: FileManager.Format | None = None) -> tuple[FileManager.Format, list[tuple[TaskQ, int]]]:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        sheet = wb.active
        
        if sheet is None:
            raise Exception("Could not read excel sheet")
        
        col_count = sheet.max_column

        headers = [str(sheet.cell(1, col).value) for col in range(1, col_count + 1)]
        if fmt is None:
            fmt = FileManager.get_file_fmt_type(headers)
        
        data = []
        for row in sheet.iter_rows(min_col=1, max_col=col_count):
            if not row[0].value: break
            data.append(
                dict(
                    (headers[i], row[i].value)
                    for i in range(col_count)
                )
            )

        wb.close()
        return fmt, [
            FileManager.decode(item, fmt) for item in data
        ]
    
    @staticmethod
    def write(path: str, tasks: list[Task], fmt: FileManager.Format):
        import openpyxl
        data = FileManager.encode_tasks(tasks, fmt)
        wb = openpyxl.Workbook(write_only=True)
        sheet = wb.create_sheet()
        
        headers = FileManager.get_headers(fmt)
        
        sheet.append(headers)
        for row in data:
            sheet.append(row)

        wb.save(path)
        wb.close()