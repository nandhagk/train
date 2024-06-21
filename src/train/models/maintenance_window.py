from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from sqlite3 import Cursor, Row


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
    def find_by_id(cur: Cursor, id: int) -> MaintenanceWindow | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT maintenance_window.* FROM maintenance_window
            WHERE
                maintenance_window.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return MaintenanceWindow.decode(row)

    @staticmethod
    def insert_many(cur: Cursor, windows: Iterable[PartialMaintenanceWindow]) -> None:
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
    def decode(row: Row) -> MaintenanceWindow:
        return MaintenanceWindow(
            row["id"],
            row["starts_at"],
            row["ends_at"],
            row["section_id"],
        )

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM maintenance_window")
