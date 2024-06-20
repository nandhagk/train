from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from train.db import cur

RawSection: TypeAlias = tuple[int, str, int, int]


@dataclass(frozen=True)
class Section:
    id: int
    line: str

    from_id: int
    to_id: int

    @staticmethod
    def find_by_id(id: int) -> Section | None:
        payload = {"id": id}

        cur.execute(
            """
            SELECT section.* FROM section
            WHERE
                section.id = :id
            """,
            payload,
        )

        raw = cur.fetchone()
        if raw is None:
            return None

        return Section.decode(raw)

    @staticmethod
    def find_by_name_and_line(name: str, line: str) -> Section | None:
        if name.endswith("YD"):
            f = t = name.removesuffix("YD").replace("-", "").strip() + "_YD"

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

        raw = cur.fetchone()
        if raw is None:
            return None

        return Section.decode(raw)

    @staticmethod
    def insert_many(sections: list[tuple[str, int, int]]) -> None:
        payload = [
            {"line": line, "from_id": from_id, "to_id": to_id}
            for line, from_id, to_id in sections
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
    def decode(raw: RawSection) -> Section:
        id, line, from_id, to_id = raw
        return Section(id, line, from_id, to_id)

    @staticmethod
    def init() -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS section (
                id INTEGER PRIMARY KEY,
                line VARCHAR(25) NOT NULL,

                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,

                FOREIGN KEY(from_id) REFERENCES station(id),
                FOREIGN KEY(to_id) REFERENCES station(id),

                UNIQUE(from_id, to_id, line)
            )
            """,
        )
