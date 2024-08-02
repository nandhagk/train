from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from sqlite3 import Cursor, Row


class RawPartialSection(TypedDict):
    line: str

    from_id: int
    to_id: int


class RawSection(RawPartialSection):
    id: int


@dataclass(frozen=True, kw_only=True)
class PartialSection:
    line: str

    from_id: int
    to_id: int


@dataclass(frozen=True)
class Section(PartialSection):
    id: int

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

        return Section.decode(cast(RawSection, row))

    @staticmethod
    def find_one_by_node_and_line(
        cur: Cursor,
        from_id: int,
        to_id: int,
        line: str,
    ) -> Section | None:
        payload = {"from_id": from_id, "to_id": to_id, "line": line}

        cur.execute(
            """
            SELECT section.* FROM section
            WHERE
                section.from_id = :from_id
                AND section.to_id = :to_id
                AND section.line = :line
            """,
            payload,
        )

        row: Row | None = cur.fetchone()
        if row is None:
            return None

        return Section.decode(cast(RawSection, row))

    @staticmethod
    def insert_many(cur: Cursor, sections: Iterable[PartialSection]) -> None:
        payload = [cast(RawPartialSection, asdict(section)) for section in sections]

        cur.executemany(
            """
            INSERT INTO section (line, from_id, to_id)
            VALUES (:line, :from_id, :to_id)
            """,
            payload,
        )

    @staticmethod
    def decode(row: RawSection) -> Section:
        return Section(**row)

    @staticmethod
    def clear(cur: Cursor) -> None:
        cur.execute("DELETE FROM section")
