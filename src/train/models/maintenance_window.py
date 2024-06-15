from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Self, TypeAlias

from train.db import cur

if TYPE_CHECKING:
    from train.models.section import Section

RawMaintenaceWindow: TypeAlias = tuple[int, str, str, int]


@dataclass(frozen=True)
class MaintenanceWindow:
    id: int
    starts_at: datetime
    ends_at: datetime

    section_id: int

    def section(self) -> Section:
        from train.models.section import Section

        section = Section.find_by_id(self.section_id)
        assert section is not None

        return section

    @classmethod
    def find_by_id(cls, id: int) -> Self | None:
        payload = {"id": id}
        res = cur.execute(
            """
            SELECT maintenance_window.* FROM maintenance_window
            WHERE
                maintenance_window.id = :id
            """,
            payload,
        )

        return cls.decode(res.fetchone())

    @classmethod
    def decode(cls, raw: RawMaintenaceWindow | None) -> Self | None:
        if raw is None:
            return None

        id, starts_at, ends_at, section_id = raw
        return cls(
            id,
            datetime.fromisoformat(starts_at),
            datetime.fromisoformat(ends_at),
            section_id,
        )

    @staticmethod
    def init() -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_window (
                id INTEGER PRIMARY KEY,

                starts_at DATETIME NOT NULL,
                ends_at DATETIME NOT NULL,

                section_id INTEGER NOT NULL,
                FOREIGN KEY(section_id) REFERENCES section(id)
            )
            """,
        )

    @staticmethod
    def clear() -> None:
        cur.execute("DELETE FROM maintenance_window")

    @staticmethod
    def insert_many(windows: list[tuple[datetime, datetime]], section_id: int) -> None:
        cur.executemany(
            "INSERT INTO maintenance_window (id, starts_at, ends_at, section_id) VALUES (NULL, ?, ?, ?)",
            [(*window, section_id) for window in windows]
        )  
