from __future__ import annotations

import logging
from collections import defaultdict
from datetime import time
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

import click
from result import Err
from waitress import serve

from train.app import app
from train.db import get_db
from train.file_management import FileManager
from train.logging import setup_logging
from train.models.task import PartialTask, Task
from train.services.slot import SlotService

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

    t0 = perf_counter()
    cur.executescript((Path.cwd() / "init.sql").read_text())
    t1 = perf_counter()

    print(t1 - t0)
    SlotService.init(cur)


@main.command()
@click.argument("src", type=ClickPath(exists=True, dir_okay=False))
@click.argument("dst", type=ClickPath(exists=False, dir_okay=False))
def schedule(src: Path, dst: Path):
    """Process tasks from src and dump them into dst."""
    con = get_db()
    cur = con.cursor()

    try:
        taskqs_per_section: dict[int, list[tuple[PartialTask, int]]] = defaultdict(list)
        skipped_data = []

        fm = FileManager.get_manager(src, dst, dst.with_suffix(".error" + dst.suffix))
        for idx, res in enumerate(fm.read(cur)):
            if isinstance(res, Err):
                skipped_data.append((idx + 1, res.err_value))
                continue
            taskq = res.value
            taskqs_per_section[taskq.section_id].append((taskq, idx + 1))

        tasks: list[Task] = []
        for section_id, rows in taskqs_per_section.items():
            logger.info("Scheduling %d", section_id)

            res = Task.insert_many(cur, [taskq for taskq, _idx in rows])
            if isinstance(res, Err):
                logger.warning("Ignoring %d", section_id, exc_info=res.err_value)
                skipped_data.extend((idx, repr(res.err_value)) for _taskq, idx in rows)
            else:
                tasks.extend(res.value)

        con.commit()
        fm.write(cur, tasks)
        fm.write_error(skipped_data)
        logger.info("Populated database and saved output file: %s", dst)

    except Exception as e:
        logger.exception("Failed to populate database from file")

        msg = f"Failed to populate database from file: {e}"
        raise click.ClickException(msg) from e


if __name__ == "__main__":
    main()
