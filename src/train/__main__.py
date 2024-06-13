import sqlite3

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
@click.argument("requested_duration", type=int)
@click.argument("priority", type=int)
@click.argument("section")
def insert(requested_duration: int, priority: int, section: str) -> None:
    """Section: STN-STN or STN YD."""
    if section.endswith("YD"):
        from_stn = to_stn = section.split()[0]
    else:
        from_stn, _, to_stn = section.partition("-")

    cur.execute(
        """
        INSERT INTO task VALUES (
            NULL, NULL, NULL,
            ?, ?,
            (SELECT id from section
            WHERE from_id = (SELECT id from station WHERE name = ?)
            AND to_id = (SELECT id from station WHERE name = ?))
        );
        """,
        (requested_duration, priority, from_stn, to_stn),
    )

    con.commit()


main()
