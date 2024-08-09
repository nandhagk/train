import logging
import sys
from datetime import time
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING

import click
import uvicorn

if sys.platform == "win32":
    from asyncio import run
else:
    from uvloop import run

from train.app import app
from train.services.node import NodeService
from train.services.section import SectionService
from train.services.train import TrainService
from train.utils import pool_factory, setup_logging

if TYPE_CHECKING:
    from asyncpg import Connection

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
@click.option("--port", type=click.IntRange(1000, 10000), default=4200)
def main(ctx: click.Context, port: int):
    if ctx.invoked_subcommand is not None:
        return

    uvicorn.run(app, port=port)


async def init_db() -> None:
    async with pool_factory() as pool, pool.acquire() as con:
        con: Connection
        await con.execute((Path.cwd() / "init.sql").read_text())

        async with con.transaction():
            await NodeService.init(con)
            await SectionService.init(con)
            await TrainService.init(con)


@main.command()
def init():
    run(init_db())


if __name__ == "__main__":
    main()
