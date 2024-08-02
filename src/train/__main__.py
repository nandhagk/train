from __future__ import annotations

import logging
from collections import defaultdict
from datetime import time, datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

import click
from result import Err
from waitress import serve

from train.app import app
from train.db import get_db, unixepoch
from train.file_management import FileManager
from train.logging import setup_logging
from train.models.section import Section
from train.models.task import PartialTask, Task
from train.services.node import NodeService
from train.services.section import SectionService
from train.services.slot import SlotService
from train.services.task import TaskService, TaskToInsert
from train.services.train import TrainService

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
@click.pass_context
@click.option("--port", type=click.IntRange(1000, 10000), default=5432)
@click.option("--debug", is_flag=True, default=False)
def main(ctx: click.Context, port: int, debug: bool):
    """Spins up a flask server."""
    if ctx.invoked_subcommand is not None:
        return

    if debug:
        app.run(port=port, debug=True)
    else:
        serve(app, port=port, url_scheme="https")


@main.command()
def init():
    """Initiliaze the database."""
    con = get_db()
    cur = con.cursor()

    cur.executescript((Path.cwd() / "init.sql").read_text())

    NodeService.init(cur)
    SectionService.init(cur)
    TrainService.init(cur)

    con.commit()

@main.command()
@click.argument("p", type=int)
@click.argument("ss", type=str)
@click.argument("se", type=str)
@click.argument("li", type=str)
@click.argument("ps", type=ClickTime())
@click.argument("pe", type=ClickTime())
@click.argument("rd", type=ClickTime())
@click.argument("dat", type=str)
def insert(p: int, ss: str, se: str, li: str, ps: time, pe: time, rd: time, dat: str):
    con = get_db()
    cur = con.cursor()

    section = Section.find_by_node_name(cur, ss, se, li)
    assert section is not None

    result = TaskService.insert_one(
        cur, 
        section.id,
        TaskToInsert(
            priority=p,
            den="DEN",
            department="DEP",
            location="LOC",
            nature_of_work="NOW",
            preferred_starts_at=ps,
            preferred_ends_at=pe,
            requested_date=datetime.fromisoformat(dat).date(),
            requested_duration=unixepoch(rd)
        )
    )

    Task.clear_tasks(cur, result.bad_tasks)

    print(result)

    con.commit()


if __name__ == "__main__":
    main()
