from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import click

con = sqlite3.connect("train.db")
cur = con.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS block (
        id INTEGER PRIMARY KEY,
        line VARCHAR(25) NOT NULL,
        name VARCHAR(25) UNIQUE NOT NULL
    )
    """,
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS free_time (
        id INTEGER PRIMARY KEY,
        starts_at DATETIME NOT NULL,
        ends_at DATETIME NOT NULL,

        block_id INTEGER NOT NULL,
        FOREIGN KEY(block_id) REFERENCES block(id)
    )
    """,
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS station (
        id INTEGER PRIMARY KEY,
        name VARCHAR(25) UNIQUE NOT NULL,

        block_id INTEGER NOT NULL,
        FOREIGN KEY(block_id) REFERENCES block(id)
    );
    """,
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS section (
        id INTEGER PRIMARY KEY,

        from_id INTEGER NOT NULL,
        to_id INTEGER NOT NULL,

        FOREIGN KEY(from_id) REFERENCES station(id)
        FOREIGN KEY(to_id) REFERENCES station(id),

        UNIQUE(from_id, to_id)
    );
    """,
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS task (
        id INTEGER PRIMARY KEY,
        starts_at DATETIME NOT NULL,
        ends_at DATETIME NOT NULL,
        requested_duration INTEGER NOT NULL,
        priority INTEGER NOT NULL,

        section_id INTEGER NOT NULL,
        FOREIGN KEY(section_id) REFERENCES section(id)
    );
    """,
)


@click.group()
def main() -> None:
    """Entrypoint."""


@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def init(data: str):
    print(data)


@main.command()
@click.argument("duration", type=int)
@click.argument("priority", type=int)
@click.argument("section")
def insert(duration: int, priority: int, section: str) -> None:
    """Section: STN-STN or STN YD."""
    if section.endswith("YD"):
        from_stn = to_stn = section.split()[0]
    else:
        from_stn, _, to_stn = section.partition("-")

    def get_block_id(stn: str) -> int:
        res = cur.execute(
            """
            SELECT block_id from station
            WHERE name = ?
            """,
            (stn,),
        )

        return res.fetchone()[0]

    def get_section_id(from_stn: str, to_stn: str) -> int:
        res = cur.execute(
            """
            SELECT id from section
            WHERE from_id = (SELECT id from station WHERE name = ?)
            AND to_id = (SELECT id from station WHERE name = ?)
            """,
            (from_stn, to_stn),
        )

        return res.fetchone()[0]

    block_id = get_block_id(from_stn)
    section_id = get_section_id(from_stn, to_stn)

    res = cur.execute(
        """
        SELECT f.starts_at FROM free_time AS f
        WHERE f.block_id = :block_id
        AND f.starts_at >= DATETIME('now', '+30 minutes')
        AND CAST((JULIANDAY(f.ends_at) - JULIANDAY(f.starts_at)) * 1440 AS REAL)
            >= :duration
        AND NOT EXISTS(
            SELECT NULL FROM task AS q
            WHERE q.section_id = :section_id
            AND f.starts_at <= q.starts_at
            AND q.ends_at <= f.ends_at
        )
        ORDER BY f.starts_at ASC
        LIMIT 1
        """,
        {"section_id": section_id, "block_id": block_id, "duration": duration},
    )

    try:
        starts_at = res.fetchone()[0]
    except TypeError:
        print("NO TIME SLOT FOR DURATION :(")
        return

    res = cur.execute(
        """
        SELECT MIN((SELECT IFNULL(
            (
                SELECT t.ends_at FROM task AS t CROSS JOIN free_time AS f
                WHERE t.section_id = :section_id
                AND f.block_id = :block_id
                AND t.ends_at >= DATETIME('now', '+30 minutes')
                AND f.starts_at <= t.starts_at
                AND f.ends_at >= t.ends_at
                AND CAST((JULIANDAY(f.ends_at) - JULIANDAY(t.ends_at)) * 1440 AS REAL)
                    >= :duration
                AND NOT EXISTS(
                    SELECT NULL FROM task AS q
                    WHERE q.section_id = :section_id
                    AND t.ends_at <= q.starts_at
                    AND q.ends_at <= f.ends_at
                )
                ORDER BY t.ends_at ASC
                LIMIT 1
            ),
            :starts_at
        )), :starts_at)
        """,
        {
            "section_id": section_id,
            "block_id": block_id,
            "duration": duration,
            "starts_at": starts_at,
        },
    )

    starts_at = datetime.strptime(res.fetchone()[0], "%Y-%m-%d %H:%M:%S")
    ends_at = starts_at + timedelta(minutes=duration)
    print(starts_at, ends_at)

    cur.execute(
        """
        INSERT INTO task VALUES (
            NULL,
            :starts_at,
            :ends_at,
            :duration,
            :priority,
            :section_id
        );
        """,
        {
            "starts_at": datetime.strftime(starts_at, "%Y-%m-%d %H:%M:%S"),
            "ends_at": datetime.strftime(ends_at, "%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "priority": priority,
            "section_id": section_id,
        },
    )

    con.commit()


main()
