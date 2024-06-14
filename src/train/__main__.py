from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pprint import pprint

import click

from train.db import con, cur
from train.models.block import Block
from train.models.maintenance_window import MaintenanceWindow
from train.models.section import Section
from train.models.station import Station
from train.models.task import Task

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

    NOTE: Does not populate free time table.
    """

    def init_block(block_name: str) -> int:
        cur.execute(
            """
            INSERT INTO block (id, name)
            VALUES (NULL, :name)
            ON CONFLICT DO NOTHING
            """,
            {"name": block_name},
        )
        con.commit()

        block = Block.find_by_name(block_name)
        assert block is not None

        return block.id

    def init_station(station_name: str, block_id: int) -> int:
        cur.execute(
            """
            INSERT INTO station (id, name, block_id)
            VALUES (NULL, :name, :block_id)
            ON CONFLICT DO NOTHING
            """,
            {"name": station_name, "block_id": block_id},
        )
        con.commit()

        station = Station.find_by_name(station_name)
        assert station is not None

        return station.id

    def init_section(id1: int, id2: int) -> None:
        cur.execute(
            """
            INSERT INTO section (id, line, from_id, to_id)
            vALUES (NULL, :line, :from_id, :to_id)
            ON CONFLICT DO NOTHING
            """,
            {"line": "UP", "from_id": id1, "to_id": id2},
        )
        con.commit()

    import json
    from pathlib import Path

    blocks = json.loads(Path(data).read_text())
    for block in blocks:
        block_id = init_block(block)
        for section in blocks[block]:
            if section[0] == section[1]:
                section[0] = section[1] = section[0] + "_YD"
            s1 = init_station(section[0], block_id)
            s2 = init_station(section[1], block_id)
            init_section(s1, s2)


@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument("length", type=int)
@click.option("--clear", is_flag=True, default=False)
def sft(data: str, length: int, clear: bool):
    """Populate the maintenance_window table."""
    import sys

    def get_block_id(block_name: str) -> int:
        block = Block.find_by_name(block_name)
        if block is None:
            print(block_name)
            print("ERROR! Block does not exist", file=sys.stderr)
            sys.exit(1)

        return block.id

    if clear:
        cur.execute("DELETE FROM maintenance_window")
        con.commit()

    from pathlib import Path

    raw = Path(data)
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

    for block_data in raw.read_text().split("\n\n"):
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
                cur.executemany(
                    "INSERT INTO maintenance_window VALUES (NULL, ?, ?, ?)",
                    [
                        (
                            datetime.now().replace(hour=0, second=0, minute=0)
                            + timedelta(days=days)
                            + st,
                            datetime.now().replace(hour=0, second=0, minute=0)
                            + timedelta(days=days)
                            + et,
                            section_id,
                        )
                        for days in range(length)
                    ],
                )
            con.commit()


@main.command()
@click.argument("duration", type=int)
@click.argument("priority", type=int)
@click.argument("name")
@click.argument("line")
def insert(duration: int, priority: int, name: str, line: str) -> None:
    """Section: STN-STN or STN YD."""
    section = Section.find_by_name_and_line(name, line)
    if section is None:
        print("Section not found")
        return

    tasks = Task.insert_greedy(timedelta(minutes=duration), priority, section.id)
    con.commit()

    pprint(tasks)


main()
