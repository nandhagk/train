from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta


def decode_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())


def encode_datetime(val: datetime) -> str:
    return val.replace(microsecond=0).isoformat()


def encode_timedelta(val: timedelta) -> int:
    return int(val.total_seconds()) // 60


sqlite3.register_adapter(datetime, encode_datetime)
sqlite3.register_adapter(timedelta, encode_timedelta)
sqlite3.register_converter("DATETIME", decode_datetime)

con = sqlite3.connect("train.db")
cur = con.cursor()
