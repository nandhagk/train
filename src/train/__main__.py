from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import click
from waitress import serve

from train.app import app
from train.db import get_db, timediff, utcnow
from train.file_management import FileManager
from train.logging import setup_logging
from train.models.block import Block, PartialBlock
from train.models.maintenance_window import MaintenanceWindow, PartialMaintenanceWindow
from train.models.section import PartialSection, Section
from train.models.station import PartialStation, Station
from train.models.task import PartialTask, Task

if TYPE_CHECKING:
    from os import PathLike

setup_logging()
logger = logging.getLogger(__name__)


class ClickPath(click.Path):
    def convert(
        self,
        value: str | PathLike[str],
        param: click.Parameter | None,
        ctx: click.Context | None,
    ):
        return Path(super().convert(value, param, ctx))  # type: ignore ()


class ClickTime(click.ParamType):
    def convert(
        self,
        value: str,
        param: click.Parameter | None,  # noqa: ARG002
        ctx: click.Context | None,  # noqa: ARG002
    ) -> time:
        return time.fromisoformat(value)


@click.group(invoke_without_command=True)
@click.option("--port", type=click.IntRange(1000, 10000), default=5432)
@click.option("--debug", is_flag=True, default=False)
def main(port: int, debug: bool):
    """Spins up a flask server."""
    if debug:
        app.run(port=port, debug=True)
    else:
        serve(app, port=port)


@main.command()
@click.argument("data", type=ClickPath(exists=True, dir_okay=False))
def init(data: Path):
    """Initiliaze the database."""
    con = get_db()
    cur = con.cursor()

    cur.executescript((Path.cwd() / "init.sql").read_text())

    try:
        blocks = json.loads(data.read_text())
        Block.insert_many(cur, [PartialBlock(name) for name in blocks])

        for block in blocks:
            block_id = Block.find_by_name(cur, block).id  # type: ignore ()

            stations: set[str] = set()
            for section in blocks[block]:
                section[0] = section[0].replace(" ", "_")
                section[1] = section[1].replace(" ", "_")

                stations.add(section[0])
                stations.add(section[1])

            Station.insert_many(
                cur,
                [PartialStation(name, block_id) for name in stations],
            )

            Section.insert_many(
                cur,
                [
                    PartialSection(
                        "UP",
                        Station.find_by_name(cur, section[0]).id,  # type: ignore ()
                        Station.find_by_name(cur, section[1]).id,  # type: ignore ()
                    )
                    for section in blocks[block]
                ]
                + [
                    PartialSection(
                        "DN",
                        Station.find_by_name(cur, section[0]).id,  # type: ignore ()
                        Station.find_by_name(cur, section[1]).id,  # type: ignore ()
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
def create_windows(data: str, length: int, clear: bool):
    """Populate the maintenance_window table."""
    con = get_db()
    cur = con.cursor()

    def get_block_id(block_name: str) -> int:
        block = Block.find_by_name(cur, block_name)
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
            MaintenanceWindow.clear(cur)

        cur.execute(
            """
            SELECT section.id, section.line, block_id FROM section
            JOIN station ON
                station.id = section.from_id
            JOIN block ON
                block.id = station.block_id
            """,
        )

        ids = cur.fetchall()
        grouped = defaultdict(list)

        for section_id, line, block_id in ids:
            grouped[(block_id, line)].append(section_id)

        today = datetime.combine(utcnow().date(), time())
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
                        cur,
                        [
                            PartialMaintenanceWindow(
                                today + timedelta(days=days) + st,
                                today + timedelta(days=days) + et,
                                section_id,
                            )
                            for days in range(length)
                        ],
                    )

        con.commit()
        logger.info("Populated maintenance_window table from data file: %s", data)

    except Exception as e:
        logger.exception("Failed to populate maintenance_window table")

        msg = f"Failed to populate maintenance_window table: {e}"
        raise click.ClickException(msg) from e


@main.command()
@click.argument("name")
@click.argument("line")
@click.option("--priority", type=int, default=1)
@click.option("--duration", type=int)
@click.option("--pref-start", type=ClickTime())
@click.option("--pref-end", type=ClickTime())
def insert(  # noqa: PLR0913
    name: str,
    line: str,
    priority: int,
    duration: int | None,
    pref_start: time | None,
    pref_end: time | None,
) -> None:
    """Section: STN-STN or STN YD."""
    con = get_db()
    cur = con.cursor()

    if duration is None and (pref_start is None or pref_end is None):
        msg = "Please either set duration or (pref_start and pref_end)"
        raise click.UsageError(msg)

    try:
        section = Section.find_by_name_and_line(cur, name, line)
        if section is None:
            logger.error("Section not found: %s - %s", name, line)

            msg = f"Section not found: {name} - {line}"
            raise click.ClickException(msg)  # noqa: TRY301

        requested_duration: timedelta | None = None
        if duration is not None:
            requested_duration = timedelta(minutes=duration)

        if pref_start is not None and pref_end is not None:
            preferred_window = timediff(pref_start, pref_end)
            if duration is None:
                requested_duration = preferred_window

            assert requested_duration is not None

            if requested_duration > preferred_window:
                msg = "Requested duration is greater than preference window."
                raise click.BadParameter(msg)  # noqa: TRY301

        else:
            assert requested_duration is not None

        Task.insert_one(
            cur,
            PartialTask(priority, requested_duration, pref_start, pref_end, section.id),
        )

        con.commit()

        logger.info(
            "Inserted new task with duration %d and priority %d for Section: %s - %s",
            requested_duration.total_seconds(),
            priority,
            name,
            line,
        )
    except Exception as e:
        logger.exception("Failed to insert task")

        msg = f"Failed to insert task: {e}"
        raise click.ClickException(msg) from e


@main.command()
@click.argument("src", type=ClickPath(exists=True, dir_okay=False))
@click.argument("dst", type=ClickPath(exists=False, dir_okay=False))
def schedule(src: Path, dst: Path):
    """Process tasks from src and dump them into dst."""
    con = get_db()
    cur = con.cursor()

    try:
        taskqs_per_section: dict[int, list[PartialTask]] = defaultdict(list)

        fmt, data = FileManager.get_manager(src).read(cur, src)
        for taskq in data:
            taskqs_per_section[taskq.section_id].append(taskq)

        tasks = []
        for section_id, taskqs in taskqs_per_section.items():
            logger.info("Scheduling section: %d", section_id)
            try:
                tasks.extend(Task.insert_many(cur, taskqs))
            except Exception:
                logger.exception("Ignoring section: %d", section_id)

        con.commit()
        FileManager.get_manager(dst).write(cur, dst, tasks, fmt)

        logger.info("Populated database and saved output file: %s", dst)
    except Exception as e:
        logger.exception("Failed to populate database from file")

        msg = f"Failed to populate database from file: {e}"
        raise click.ClickException(msg) from e


if __name__ == "__main__":
    main()
