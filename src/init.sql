DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS maintenance_window;
DROP TABLE IF EXISTS section;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS block;

CREATE TABLE block (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,

    UNIQUE(name)
);

CREATE TABLE station (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,

    block_id INTEGER NOT NULL,
    FOREIGN KEY(block_id) REFERENCES block(id),

    UNIQUE(name)
);


CREATE TABLE section (
    id INTEGER PRIMARY KEY,
    line TEXT NOT NULL,

    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,

    FOREIGN KEY(from_id) REFERENCES station(id),
    FOREIGN KEY(to_id) REFERENCES station(id),

    UNIQUE(from_id, to_id, line)
);

CREATE TABLE maintenance_window (
    id INTEGER PRIMARY KEY,

    starts_at DATETIME NOT NULL,
    ends_at DATETIME NOT NULL,

    section_id INTEGER NOT NULL,
    FOREIGN KEY(section_id) REFERENCES section(id)
);

CREATE TABLE task (
    id INTEGER PRIMARY KEY,
    starts_at DATETIME NOT NULL,
    ends_at DATETIME NOT NULL,
    preferred_starts_at TIME,
    preferred_ends_at TIME,
    requested_duration INTEGER NOT NULL,
    priority INTEGER NOT NULL,

    maintenance_window_id INTEGER NOT NULL,
    FOREIGN KEY(maintenance_window_id) REFERENCES maintenance_window(id)
);
