from __future__ import annotations

import sqlite3
from datetime import datetime, time, timedelta


def encode_datetime(val: datetime) -> str:
    return val.replace(microsecond=0).isoformat()


def encode_timedelta(val: timedelta) -> float:
    return val.total_seconds()


def encode_time(val: time) -> str:
    return val.isoformat()


sqlite3.register_adapter(datetime, encode_datetime)
sqlite3.register_adapter(timedelta, encode_timedelta)
sqlite3.register_adapter(time, encode_time)

con = sqlite3.connect("train.db")
cur = con.cursor()
