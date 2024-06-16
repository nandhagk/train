from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint
import logging

import click

from train.db import con, cur
from train.models.block import Block
from train.models.maintenance_window import MaintenanceWindow
from train.models.section import Section
from train.models.station import Station
from train.models.task import Task

#Logger config; Create directory if it doesnt already exist
log_folder = Path(__file__).resolve().parent / 'log'
log_folder.mkdir(parents=True, exist_ok=True)
log_file = log_folder / 'errors.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)    

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
            block_id = Block.find_by_name(block).id

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
                        Station.find_by_name(section[0]).id,
                        Station.find_by_name(section[1]).id,
                    )
                    for section in blocks[block]
                ],
            )

        con.commit()
        logger.info("Initialized database with dummy data from file: %s", data)

    except Exception as e:
        logger.error("Failed to initialize database with dummy data: %s", str(e))
        raise click.ClickException(f"Failed to initialize database with dummy data: {e}")


@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument("length", type=int)
@click.option("--clear", is_flag=True, default=False)
def sft(data: str, length: int, clear: bool):
    """Populate the maintenance_window table."""

    def get_block_id(block_name: str) -> int:
        block = Block.find_by_name(block_name)
        if block is None:
            logger.error("Invalid time data file. Block `%s` does not exist", block_name)
            raise click.ClickException(f"Invalid time data file. Block `{block_name}` does not exist")
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
                        section_id,# Configure logging
logging.basicConfig(filename='train_app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
                    )

        con.commit()
        logger.info("Populated maintenance_window table from data file: %s", data)

    except Exception as e:
        logger.error("Failed to populate maintenance_window table: %s", str(e))
        raise click.ClickException(f"Failed to populate maintenance_window table: {e}")


@main.command()
@click.argument("name")
@click.argument("line")
def defrag(name: str, line: str) -> None:
    """Reschedules all future tasks inorder to remove gaps."""
    try:
        section = Section.find_by_name_and_line(name, line)
        if section is None:
            logger.error("Section not found: %s - %s", name, line)
            raise click.ClickException(f"Section not found: {name} - {line}")

        tasks = sorted(
            Task.delete_future_tasks(section.id),
            key=lambda task: (task.priority, task.requested_duration),
            reverse=True,
        )

        newtasks = []
        for task in tasks:
            ts = Task.insert_greedy(task.requested_duration, task.priority, section.id)
            newtasks.extend(ts)

        con.commit()
        logger.info("Defragmented tasks for Section: %s - %s", name, line)
        pprint(newtasks)

    except Exception as e:
        logger.error("Failed to defragment tasks: %s", str(e))
        raise click.ClickException(f"Failed to defragment tasks: {e}")


@main.command()
@click.argument("duration", type=int)
@click.argument("priority", type=int)
@click.argument("name")
@click.argument("line")
def insert(duration: int, priority: int, name: str, line: str) -> None:
    """Section: STN-STN or STN YD."""
    try:
        section = Section.find_by_name_and_line(name, line)
        if section is None:
            logger.error("Section not found: %s - %s", name, line)
            raise click.ClickException(f"Section not found: {name} - {line}")

        tasks = Task.insert_greedy(timedelta(minutes=duration), priority, section.id)
        con.commit()

        logger.info("Inserted new task with duration %d and priority %d for Section: %s - %s", duration, priority, name, line)
        pprint(tasks)

    except Exception as e:
        logger.error("Failed to insert task: %s", str(e))
        raise click.ClickException(f"Failed to insert task: {e}")


if __name__ == "__main__":
    main()
