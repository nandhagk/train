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
        name VARCHAR(25) NOT NULL,
        UNIQUE(line, name)
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
        name VARCHAR(25) NOT NULL,

        block_id INTEGER NOT NULL,
        FOREIGN KEY(block_id) REFERENCES block(id),
        UNIQUE(name, block_id)
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
    """
    Puts some dummy data in the database.
    NOTE: Does not populate free time table.
    """
    def init_block(block_name: str):
        block_ids = [0, 0]
        for line in ("UP", "DN"):
            cur.execute(
                """
                INSERT INTO block (id, line, name)
                SELECT NULL, ?, ? WHERE
                NOT EXISTS (SELECT * from block where name = ? and line = ?)
                """,
                (line, block_name, block_name, line)
            )
            con.commit()

            cur.execute("select id from block where name = ?", (block_name,))
            block_ids[line == "DN"] = cur.fetchall()[0][0]

        return block_ids

    def init_station(station_name: str, block_id: int):
        try:
            cur.execute(
                """
                INSERT INTO station (id, name, block_id)
                SELECT NULL, ?, ? WHERE
                NOT EXISTS (SELECT * from station where name = ? and block_id = ?)
                """,
                (station_name, block_id, station_name, block_id)
            )
            con.commit()

            cur.execute("select id from station where name = ? and block_id = ?", (station_name, block_id))
            return cur.fetchall()[0][0]
        except:
            return None
        
    def init_section(id1: int, id2: int):
        cur.execute(
            """
            INSERT INTO section (id, from_id, to_id)
            SELECT NULL, ?, ? WHERE
            NOT EXISTS (SELECT * from section where from_id = ? and to_id = ?)
            """,
            (id1, id2, id1, id2)
        )
        con.commit()

    import json
    from pathlib import Path
    blocks = json.loads(Path(data).read_text())
    for block in blocks:
        for block_id in init_block(block):
            for section in blocks[block]:
                if section[0] == section[1]:
                    section[0] = section[1] = section[0] + "_YD"
                s1 = init_station(section[0], block_id)
                s2 = init_station(section[1], block_id)

                if s1 == None or s2 == None:
                    print(f"Skipping `{block}`: {tuple(section)}")
                    continue

                init_section(s1, s2)

@main.command()
@click.argument("data", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument("length", type=int)
@click.option("--clear", is_flag = True, default = False)
def sft(data: str, length: int, clear: bool):
    """
    Populateds the free_time table.
    """
    import sys

    def get_block_id(block_name: str, ln: str):
        cur.execute("SELECT id FROM block WHERE name=? and line=?", (block_name, ln))
        result = cur.fetchone()
        if result is None:
            print(block_name)
            print("ERROR! Block does not exist", file=sys.stderr)
            sys.exit(1)

        return result[0]

    if clear:
        cur.execute("DELETE FROM free_time")
        con.commit()

    from pathlib import Path
    from datetime import date
    raw = Path(data)
    for block_data in raw.read_text().split('\n\n'):
        lines = block_data.splitlines()
        block_name = lines[0][1:]
        for line in lines[1:]:
            ln, st, et = line.split()
            st = timedelta(hours=int(st[:2]), minutes=int(st[2:]))
            et = timedelta(hours=int(et[:2]), minutes=int(et[2:]))
            bid = get_block_id(block_name, ln)
            cur.executemany("INSERT INTO free_time VALUES (NULL, ?, ?, ?)",
                [
                    (
                        bid,
                        datetime.strftime(datetime.now().replace(hour = 0, second = 0, minute = 0) + timedelta(days=days) + st, "%Y-%m-%d %H:%M:%S"),
                        datetime.strftime(datetime.now().replace(hour = 0, second = 0, minute = 0) + timedelta(days=days) + et, "%Y-%m-%d %H:%M:%S")
                    )
                    for days in range(length)
            ])
            con.commit()



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
