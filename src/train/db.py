from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time, timedelta


def combine(date, time):
    return datetime.combine(date, time, UTC)


def encode_datetime(val: datetime) -> str:
    """Encode a `datetime.datetime`  into UNIX Timestamp."""
    return val.replace(microsecond=0).isoformat()


def encode_timedelta(val: timedelta) -> int:
    """Encode a `datetime.timedelta`  into seconds."""
    return round(val.total_seconds())


def encode_date(val: date) -> str:
    """Encode a `datetime.date`  into ISO format."""
    return val.isoformat()


def decode_date(raw: str) -> date:
    """Decode a ISO format string to `datetime.date`."""
    return datetime.fromisoformat(raw).date()

def encode_time(val: time) -> str:
    """Encode a `datetime.time`  into ISO format."""
    return val.isoformat()


def decode_datetime(raw: str) -> datetime:
    """Decode a ISO format string to `datetime.datetime`."""
    return datetime.fromisoformat(raw).replace(tzinfo=UTC)


def decode_timedelta(raw: int) -> timedelta:
    """Decode a ISO format string to `datetime.timedelta`."""
    return timedelta(seconds=raw)


def decode_time(raw: str) -> time:
    """Decode a ISO format string to `datetime.time`."""
    return time.fromisoformat(raw)


def utcnow() -> datetime:
    """Get current time."""
    return datetime.now(UTC)


def unixepoch(time: time) -> timedelta:
    """Get `datetime.timedelta` from `datetime.time`."""
    return datetime.combine(date.min, time) - datetime.min


def timediff(start: time, stop: time) -> timedelta:
    """Get difference between two times."""
    diff = datetime.combine(date.min, stop) - datetime.combine(date.min, start)
    if stop <= start:
        diff += timedelta(days=1)

    return diff


sqlite3.register_adapter(datetime, encode_datetime)
sqlite3.register_adapter(timedelta, encode_timedelta)
sqlite3.register_adapter(time, encode_time)
sqlite3.register_adapter(date, encode_date)

sqlite3.register_converter("DATETIME", lambda raw: decode_datetime(raw.decode()))
sqlite3.register_converter("TIME", lambda raw: decode_time(raw.decode()))
sqlite3.register_converter("DATE", lambda raw: decode_date(raw.decode()))


def get_db() -> sqlite3.Connection:
    """Create db connection."""
    con = sqlite3.connect("./tmp/train.db", detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row

    con.execute("PRAGMA journal_mode=WAL")

    return con
