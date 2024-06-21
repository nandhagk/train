from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from train.db import cur

if TYPE_CHECKING:
    from collections.abc import Iterable

RawSection: TypeAlias = tuple[int, str, int, int]


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
    def insert_many(sections: Iterable[PartialSection]) -> None:
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
    def decode(raw: RawSection) -> Section:
        id, line, from_id, to_id = raw
        return Section(id, line, from_id, to_id)
