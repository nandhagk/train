from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


@dataclass(frozen=True)
class PartialSection:
    line: str

    from_id: int
    to_id: int


@dataclass(frozen=True)
class Section:
    id: int
    line: str

    from_id: int
    to_id: int

    @staticmethod
    def find_by_id(cur: Cursor, id: int) -> Section | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT section.* FROM section
            WHERE
                section.id = :id
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Section.decode(row)

    @staticmethod
    def find_by_name_and_line(cur: Cursor, name: str, line: str) -> Section | None:
        name = name.replace(" ", "_").replace("-YD", "_YD")

        if "-" not in name:
            f = t = name
        else:
            f, _, t = name.partition("-")
            f = f.strip()
            t = t.strip()

        payload = {"f": f, "t": t, "line": line}

        cur.execute(
            """
            SELECT section.* FROM section
            WHERE
                section.line = :line
                AND section.from_id = (
                    SELECT station.id FROM station
                    WHERE
                        station.name = :f
                )
                AND section.to_id = (
                    SELECT station.id FROM station
                    WHERE
                        station.name = :t
                )
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Section.decode(row)

    @staticmethod
    def insert_many(cur: Cursor, sections: Iterable[PartialSection]) -> None:
        payload = [
            {"line": section.line, "from_id": section.from_id, "to_id": section.to_id}
            for section in sections
        ]

        cur.executemany(
            """
            INSERT INTO section (line, from_id, to_id)
            vALUES (:line, :from_id, :to_id)
            ON CONFLICT DO NOTHING
            """,
            payload,
        )

    @staticmethod
    def decode(row: Row) -> Section:
        return Section(row["id"], row["line"], row["from_id"], row["to_id"])
