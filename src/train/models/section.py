from __future__ import annotations

from dataclasses import dataclass
from typing import Self, TypeAlias

from train.db import cur

RawSection: TypeAlias = tuple[int, str, int, int]


@dataclass(frozen=True)
class Section:
    id: int
    line: str

    from_id: int
    to_id: int

    @classmethod
    def find_by_id(cls, id: int) -> Self | None:
        payload = {"id": id}

        res = cur.execute(
            """
            SELECT section.* FROM section
            WHERE
                section.id = :id
            """,
            payload,
        )

        return cls.decode(res.fetchone())

    @classmethod
    def find_by_name_and_line(
        cls,
        name: str,
        line: str,
    ) -> Self | None:
        if "-" in name:
            f, _, t = name.partition("-")
        else:
            f = t = name.replace(" ", "_")

        payload = {"f": f, "t": t, "line": line}

        res = cur.execute(
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

        return cls.decode(res.fetchone())

    @classmethod
    def decode(cls, raw: RawSection | None) -> Self | None:
        if raw is None:
            return None

        id, line, from_id, to_id = raw
        return cls(id, line, from_id, to_id)

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

    @staticmethod
    def insert_many(sections: list[tuple[str, int, int]]) -> None:
        cur.executemany(
            """
            INSERT INTO section (id, line, from_id, to_id)
            vALUES (NULL, :line, :from_id, :to_id)
            ON CONFLICT DO NOTHING
            """,
            sections,
        )