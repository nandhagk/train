DROP TABLE IF EXISTS slot;
DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS train;
DROP TABLE IF EXISTS section;
DROP TABLE IF EXISTS node;

CREATE TABLE node (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,

    UNIQUE(name, position)
);

CREATE TABLE section (
    id INTEGER PRIMARY KEY,
    line TEXT NOT NULL,

    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,

    FOREIGN KEY(from_id) REFERENCES node(id),
    FOREIGN KEY(to_id) REFERENCES node(id),

    UNIQUE(from_id, to_id, line)
);

CREATE TABLE slot (
    id INTEGER PRIMARY KEY,

    starts_at DATETIME NOT NULL,
    ends_at DATETIME NOT NULL,

    section_id INTEGER NOT NULL,

    task_id INTEGER,
    train_id INTEGER,

    FOREIGN KEY(task_id) REFERENCES task(id),
    FOREIGN KEY(train_id) REFERENCES train(id),

    CHECK(
        (task_id IS NOT NULL AND train_id IS NULL)
        OR (task_id IS NULL AND train_id IS NOT NULL)
    )
);

CREATE TABLE task (
    id INTEGER PRIMARY KEY,

    department TEXT NOT NULL,
    den TEXT NOT NULL,
    nature_of_work TEXT NOT NULL,
    location TEXT NOT NULL,

    preferred_starts_at TIME,
    preferred_ends_at TIME,
    requested_duration INTEGER NOT NULL,
    priority INTEGER NOT NULL
);

CREATE TABLE train (
    id INTEGER PRIMARY KEY,

    number TEXT NOT NULL,
    name TEXT NOT NULL,

    UNIQUE(number)
);
