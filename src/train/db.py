from __future__ import annotations

import sqlite3
from datetime import datetime


def decode_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())


def encode_datetime(val: datetime) -> str:
    return val.replace(microsecond=0).isoformat()


sqlite3.register_adapter(datetime, encode_datetime)
sqlite3.register_converter("DATETIME", decode_datetime)

con = sqlite3.connect("train.db")
cur = con.cursor()
