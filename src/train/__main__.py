from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path

import click

from train.db import con, cur
from train.models.block import Block
from train.models.maintenance_window import MaintenanceWindow
from train.models.section import Section
from train.models.station import Station
from train.models.task import Task

logging.basicConfig(
    filename=Path.cwd() / "train.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger()

Block.init()
Station.init()
Section.init()
MaintenanceWindow.init()
Task.init()


@click.group()
def main() -> None:
    """Entrypoint."""


@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def init(data: str):
    """
    Put some dummy data in the database.

    NOTE: Does not populate maintenance_window table.
    """
    try:
        blocks = json.loads(Path(data).read_text())
        Block.insert_many(blocks)

        for block in blocks:
            block_id = Block.find_by_name(block).id  # type: ignore ()

            stations: set[str] = set()
            for section in blocks[block]:
                if section[0] == section[1]:
                    section[0] = section[1] = section[0] + "_YD"
                stations.add(section[0])
                stations.add(section[1])

            Station.insert_many(list(stations), block_id)
            Section.insert_many(
                [
                    (
                        "UP",
                        Station.find_by_name(section[0]).id,  # type: ignore ()
                        Station.find_by_name(section[1]).id,  # type: ignore ()
                    )
                    for section in blocks[block]
                ],
            )

        con.commit()
        logger.info("Initialized database with dummy data from file: %s", data)

    except Exception as e:
        logger.exception("Failed to initialize database with dummy data")

        msg = f"Failed to initialize database with dummy data: {e}"
        raise click.ClickException(msg) from e


@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument("length", type=int)
@click.option("--clear", is_flag=True, default=False)
def sft(data: str, length: int, clear: bool):
    """Populate the maintenance_window table."""

    def get_block_id(block_name: str) -> int:
        block = Block.find_by_name(block_name)
        if block is None:
            logger.error(
                "Invalid time data file. Block `%s` does not exist",
                block_name,
            )
            msg = f"Invalid time data file. Block `{block_name}` does not exist"
            raise click.ClickException(msg)

        return block.id

    try:
        if clear:
            MaintenanceWindow.clear()

        res = cur.execute(
            """
            SELECT section.id, section.line, block_id from section
            JOIN station ON
                station.id = section.from_id
            JOIN block ON
                block.id = station.block_id
            """,
        )

        ids = res.fetchall()
        grouped = defaultdict(list)

        for section_id, line, block_id in ids:
            grouped[(block_id, line)].append(section_id)

        for block_data in Path(data).read_text().split("\n\n"):
            lines = block_data.splitlines()
            block_name = lines[0][1:]
            for line in lines[1:]:
                ln, st, et = line.split()
                st = timedelta(hours=int(st[:2]), minutes=int(st[2:]))
                et = timedelta(hours=int(et[:2]), minutes=int(et[2:]))

                if et < st:
                    et += timedelta(hours=24)

                bid = get_block_id(block_name)
                for section_id in grouped[(bid, ln)]:
                    MaintenanceWindow.insert_many(
                        [
                            (
                                datetime.now().replace(hour=0, second=0, minute=0)
                                + timedelta(days=days)
                                + st,
                                datetime.now().replace(hour=0, second=0, minute=0)
                                + timedelta(days=days)
                                + et,
                            )
                            for days in range(length)
                        ],
                        section_id,
                    )

        con.commit()
        logger.info("Populated maintenance_window table from data file: %s", data)

    except Exception as e:
        logger.exception("Failed to populate maintenance_window table")

        msg = f"Failed to populate maintenance_window table: {e}"
        raise click.ClickException(msg) from e


# @main.command()
# @click.argument("name")
# @click.argument("line")
# def defrag(name: str, line: str) -> None:
#     """Reschedules all future tasks inorder to remove gaps."""
#     try:
#         section = Section.find_by_name_and_line(name, line)
#         if section is None:
#             logger.error("Section not found: %s - %s", name, line)

#             msg = f"Section not found: {name} - {line}"
#             raise click.ClickException(msg)

#         tasks = sorted(
#             Task.delete_future_tasks(section.id),
#             key=lambda task: (task.priority, task.requested_duration),
#             reverse=True,
#         )

#         newtasks = []
#         for task in tasks:
#            ts = Task.insert_greedy(task.requested_duration, task.priority, section.id)
#            newtasks.extend(ts)

#         con.commit()
#         logger.info("Defragmented tasks for Section: %s - %s", name, line)
#         pprint(newtasks)

#     except Exception as e:
#         logger.exception("Failed to defragment tasks")

#         msg = f"Failed to defragment tasks: {e}"
#         raise click.ClickException(msg) from e


# @main.command()
# @click.argument("duration", type=int)
# @click.argument("priority", type=int)
# @click.argument("name")
# @click.argument("line")
# def insert(duration: int, priority: int, name: str, line: str) -> None:
#     """Section: STN-STN or STN YD."""
#     try:
#         section = Section.find_by_name_and_line(name, line)
#         if section is None:
#             logger.error("Section not found: %s - %s", name, line)

#             msg = f"Section not found: {name} - {line}"
#             raise click.ClickException(msg)

#         tasks = Task.insert_greedy(timedelta(minutes=duration), priority, section.id)
#         con.commit()

#         logger.info(
#             "Inserted new task with duration %d and priority %d for Section: %s - %s",
#             duration,
#             priority,
#             name,
#             line,
#         )
#         pprint(tasks)

#     except Exception as e:
#         logger.exception("Failed to insert task")

#         msg = f"Failed to insert task: {e}"
#         raise click.ClickException(msg) from e


if __name__ == "__main__":
    # main()

    for _ in range(3):
        Task.insert_preferred(
            time(),
            time(),
            1,
            1,
            requested_duration=timedelta(hours=1),
        )
        con.commit()

    print("HELLo")
    Task.insert_preferred(
        time(hour=23, minute=30),
        time(),
        2,
        1,
        requested_duration=timedelta(minutes=30),
    )
    con.commit()
