from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time, timedelta


def encode_datetime(val: datetime) -> str:
    """Encode a `datetime.datetime`  into ISO format."""
    return val.replace(microsecond=0).isoformat()


def encode_timedelta(val: timedelta) -> int:
    """Encode a `datetime.timedelta`  into seconds."""
    return round(val.total_seconds())


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


sqlite3.register_adapter(datetime, encode_datetime)
sqlite3.register_adapter(timedelta, encode_timedelta)
sqlite3.register_adapter(time, encode_time)

con = sqlite3.connect("./tmp/train.db")
cur = con.cursor()
