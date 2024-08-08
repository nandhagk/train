import logging
from datetime import date, datetime, time, timedelta
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from typing import Final
from zoneinfo import ZoneInfo

from asyncpg import Pool, create_pool
from msgspec.json import Encoder

TZ: Final = ZoneInfo("Asia/Kolkata")
ENCODER: Final = Encoder()


def combine(date: date, time: time):
    """Create a `datetime.datetime`  from a `datetime.date` and `datetime.time` ."""
    return datetime.combine(date, time, TZ)


def encode_datetime(val: datetime) -> str:
    """Encode a `datetime.datetime`  into ISO format."""
    return val.replace(microsecond=0).isoformat()


def encode_timedelta(val: timedelta) -> int:
    """Encode a `datetime.timedelta`  into seconds."""
    return round(val.total_seconds())


def encode_date(val: date) -> str:
    """Encode a `datetime.date`  into ISO format."""
    return val.isoformat()


def decode_date(raw: str) -> date:
    """Decode a ISO format string to `datetime.date`."""
    return date.fromisoformat(raw)


def encode_time(val: time) -> str:
    """Encode a `datetime.time`  into ISO format."""
    return val.isoformat()


def decode_datetime(raw: str) -> datetime:
    """Decode a ISO format string to `datetime.datetime`."""
    return datetime.fromisoformat(raw).replace(tzinfo=TZ)


def decode_timedelta(raw: int) -> timedelta:
    """Decode a ISO format string to `datetime.timedelta`."""
    return timedelta(seconds=raw)


def decode_time(raw: str) -> time:
    """Decode a ISO format string to `datetime.time`."""
    return time.fromisoformat(raw)


def now() -> datetime:
    """Get current time."""
    return datetime.now(TZ)


def unixepoch(time: time) -> timedelta:
    """Get `datetime.timedelta` from `datetime.time`."""
    return combine(date.min, time) - datetime.min


def timediff(start: time, stop: time) -> timedelta:
    """Get difference between two times."""
    diff = combine(date.min, stop) - combine(date.min, start)
    if stop <= start:
        diff += timedelta(days=1)

    return diff


def pool_factory() -> Pool:
    pool = create_pool(
        user="postgres",
        password="pass",  # noqa: S106
        database="ftcb",
        host="127.0.0.1",
    )

    assert pool is not None
    return pool


def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        handlers=[
            RotatingFileHandler(
                "train.log",
                maxBytes=32 * 1024 * 1024,
                backupCount=5,
            ),
            StreamHandler(),
        ],
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)-7s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
