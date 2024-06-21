from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from train.db import cur, decode_datetime

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime


RawMaintenaceWindow: TypeAlias = tuple[int, str, str, int]


@dataclass(frozen=True)
class PartialMaintenanceWindow:
    starts_at: datetime
    ends_at: datetime

    section_id: int


@dataclass(frozen=True)
class MaintenanceWindow:
    id: int
    starts_at: datetime
    ends_at: datetime

    section_id: int

    @staticmethod
    def find_by_id(id: int) -> MaintenanceWindow | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT maintenance_window.* FROM maintenance_window
            WHERE
                maintenance_window.id = :id
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return MaintenanceWindow.decode(raw)

    @staticmethod
    def insert_many(windows: Iterable[PartialMaintenanceWindow]) -> None:
        payload = [
            {
                "starts_at": window.starts_at,
                "ends_at": window.ends_at,
                "section_id": window.section_id,
            }
            for window in windows
        ]

        cur.executemany(
            """
            INSERT INTO maintenance_window (starts_at, ends_at, section_id)
            VALUES (:starts_at, :ends_at, :section_id)
            """,
            payload,
        )

    @staticmethod
    def decode(raw: RawMaintenaceWindow) -> MaintenanceWindow:
        id, starts_at, ends_at, section_id = raw
        return MaintenanceWindow(
            id,
            decode_datetime(starts_at),
            decode_datetime(ends_at),
            section_id,
        )

    @staticmethod
    def clear() -> None:
        cur.execute("DELETE FROM maintenance_window")
