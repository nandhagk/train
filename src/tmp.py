import json    
from pathlib import Path
import sqlite3
from random import randint



con = sqlite3.connect("train.db")
cur = con.cursor()

def init_block(block_name: str):
    line = ("UP" if randint(0, 1) else "DN")
    cur.execute(
        """
        INSERT INTO block (id, line, name)
        SELECT NULL, ?, ? WHERE
        NOT EXISTS (SELECT * from block where name = ?)
        """,
        (line, block_name, block_name)
    )
    con.commit()

    cur.execute("select id from block where name = ?", (block_name,))
    return cur.fetchall()[0][0]

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


def init(data: str):
    blocks = json.loads(Path(data).read_text())
    for block in blocks:
        block_id = init_block(block)
        for section in blocks[block]:
            if section[0] == section[1]:
                section[0] = section[1] = section[0] + "_YD"
            s1 = init_station(section[0], block_id)
            s2 = init_station(section[1], block_id)

            if s1 == None or s2 == None:
                print(f"Skipping `{block}`: {tuple(section)}")
                continue

            init_section(s1, s2)


if __name__ == '__main__':
    init("C:\\Users\\kaush\\Downloads\\github\\train\\src\\tmp\\mas.json")