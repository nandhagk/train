DROP TABLE IF EXISTS completed_task;
DROP TABLE IF EXISTS requested_task;
DROP TABLE IF EXISTS slot;
DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS train;
DROP TABLE IF EXISTS section;
DROP TABLE IF EXISTS node;

CREATE TABLE node (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    name TEXT NOT NULL,
    position INTEGER NOT NULL,

    UNIQUE(name, position)
);

CREATE TABLE section (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    line TEXT NOT NULL,

    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,

    FOREIGN KEY(from_id) REFERENCES node(id),
    FOREIGN KEY(to_id) REFERENCES node(id),

    UNIQUE(line, from_id, to_id)
);


CREATE TABLE task (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    department TEXT NOT NULL,
    den TEXT NOT NULL,
    nature_of_work TEXT NOT NULL,
    block TEXT NOT NULL,
    location TEXT NOT NULL,

    preferred_starts_at TIME NOT NULL,
    preferred_ends_at TIME NOT NULL,

    requested_date DATE NOT NULL,
    requested_duration INTERVAL NOT NULL
);

CREATE TABLE train (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    name TEXT NOT NULL,
    number TEXT NOT NULL,

    UNIQUE(number)
);

CREATE TABLE slot (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,

    priority INTEGER NOT NULL,
    section_id INTEGER NOT NULL,

    task_id INTEGER,
    train_id INTEGER,

    FOREIGN KEY(section_id) REFERENCES section(id),
    FOREIGN KEY(task_id) REFERENCES task(id),
    FOREIGN KEY(train_id) REFERENCES train(id),

    CHECK(
        (task_id IS NOT NULL AND train_id IS NULL)
        OR (task_id IS NULL AND train_id IS NOT NULL)
    )
);

CREATE TABLE requested_task (
    id INTEGER PRIMARY KEY REFERENCES task(id),

    priority INTEGER NOT NULL,
    section_id INTEGER NOT NULL,

    FOREIGN KEY(section_id) REFERENCES section(id)
);

CREATE TABLE completed_task (
    id INTEGER PRIMARY KEY REFERENCES task(id),

    output INTEGER NOT NULL
);

CREATE INDEX slot_priority_ix ON slot(priority);
CREATE INDEX slot_starts_at_ix ON slot(starts_at);
CREATE INDEX slot_ends_at_ix ON slot(ends_at);
