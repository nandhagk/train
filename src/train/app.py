from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from pathlib import Path

from flask import Flask, request, send_file

from train.db import get_db
from train.file_management import FileManager
from train.models.task import PartialTask, Task

app = Flask("app")


@app.get("/")
def idk():
    """Return html."""
    return send_file((Path.cwd() / "client" / "index.html").as_posix())


count = 0

logger = getLogger(__name__)


@app.post("/request")
def handle_form():
    """Handle form."""
    global count

    f = request.files["fileInput"]
    assert f.filename is not None

    name, _, ext = f.filename.rpartition(".")

    src = Path.cwd() / "tmp" / (str(count := count + 1) + "." + ext)
    f.save(src.as_posix())

    con = get_db()
    cur = con.cursor()

    dst = src.parent / (str(count := count + 1) + "." + ext)

    try:
        taskqs_per_section: dict[int, list[PartialTask]] = defaultdict(list)

        fmt, data = FileManager.get_manager(src).read(cur, src)
        for taskq in data:
            taskqs_per_section[taskq.section_id].append(taskq)

        tasks = []
        for section_id, taskqs in taskqs_per_section.items():
            logger.info("Scheduling section: %d", section_id)
            try:
                tasks.extend(Task.insert_many(cur, taskqs))
            except Exception:  # noqa: BLE001
                logger.warning("Ignoring section: %d", section_id)

        FileManager.get_manager(dst).write(cur, dst, tasks, fmt)

        logger.info("Populated database and saved output file: %s", dst)
    except Exception as e:
        logger.exception("Failed to populate database from file")
        return repr(e)

    return send_file(
        dst.as_posix(),
        as_attachment=True,
        download_name=f"{name}_output.{ext}",
    )
