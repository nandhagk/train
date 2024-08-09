from collections.abc import Iterable

from asyncpg import Connection, Record

from train.models.section import PartialSection, Section


class SectionRepository:
    @staticmethod
    async def find_one_by_id(con: Connection, id: int) -> Section | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT section.* FROM section
            WHERE
                section.id = $1
            """,
            id,
        )

        if row is None:
            return None

        return Section.decode(row)

    @staticmethod
    async def find_one_by_line_and_nodes(
        con: Connection,
        line: str,
        from_id: int,
        to_id: int,
    ) -> Section | None:
        row: Record | None = await con.fetchrow(
            """
            SELECT section.* FROM section
            WHERE
                section.line = $1
                AND section.from_id = $2
                AND section.to_id = $3
            """,
            line,
            from_id,
            to_id,
        )

        if row is None:
            return None

        return Section.decode(row)

    @staticmethod
    async def find_one_by_line_and_names(
        con: Connection,
        line: str,
        start: str,
        end: str,
    ) -> Section | None:
        # TODO: Fix this  # noqa: FIX002, TD002, TD003
        row: Record | None = await con.fetchrow(
            """
            SELECT section.* FROM section
            WHERE
                section.line = $1
                AND section.from_id = (
                    SELECT node.id FROM node
                    WHERE
                        node.name = $2
                        AND node.position = 2
                )
                AND section.to_id = (
                    SELECT node.id FROM node
                    WHERE
                        node.name = $3
                        AND node.position = 1
                )
            """,
            line,
            start,
            end,
        )

        if row is None:
            return None

        return Section.decode(row)

    @staticmethod
    async def find_all(con: Connection) -> list[Section]:
        rows: list[Record] = await con.fetch(
            """
            SELECT section.* FROM section
            """,
        )

        return [Section.decode(row) for row in rows]

    @staticmethod
    async def insert_one(con: Connection, section: PartialSection) -> Section:
        row: Record = await con.fetchrow(
            """
            INSERT INTO section
                (line, from_id, to_id)
            VALUES
                ($1, $2, $3)
            RETURNING *
            """,
            *section.encode()[1:],
        )

        return Section.decode(row)

    @staticmethod
    async def insert_many(
        con: Connection,
        sections: Iterable[PartialSection],
    ) -> list[Section]:
        rows: list[Record] = await con.fetch(
            """
            INSERT INTO section
                (line, from_id, to_id)
            (
                SELECT s.line, s.from_id, s.to_id
                FROM unnest($1::section[]) as s
            )
            RETURNING *
            """,
            [section.encode() for section in sections],
        )

        return [Section.decode(row) for row in rows]
