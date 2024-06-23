from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, request, send_file
from result import Err

from train.db import get_db
from train.file_management import FileManager
from train.models.task import PartialTask, Task

app = Flask("app")


@app.get("/")
def idk():
    """Return html."""
    return send_file((Path.cwd() / "client" / "index.html").as_posix())


logger = getLogger(__name__)


@app.post("/request")
def handle_form():
    """Handle form."""
    f = request.files["fileInput"]
    assert f.filename is not None

    name, _, ext = f.filename.rpartition(".")

    with (
        NamedTemporaryFile(suffix=f".{ext}") as src,
        NamedTemporaryFile(suffix=f".{ext}") as dst,
    ):
        src_path = Path(src.name)
        dst_path = Path(dst.name)

        f.save(src_path)

        con = get_db()
        cur = con.cursor()

        try:
            taskqs_per_section: dict[int, list[PartialTask]] = defaultdict(list)

            fm = FileManager.get_manager(src_path, dst_path)
            for taskq in fm.read(cur):
                taskqs_per_section[taskq.section_id].append(taskq)

            tasks: list[Task] = []
            for section_id, taskqs in taskqs_per_section.items():
                logger.info("Scheduling %d", section_id)
                for res in Task.insert_many(cur, taskqs):
                    if isinstance(res, Err):
                        logger.warning(res.err_value)
                    else:
                        tasks.append(res.value)

            fm.write(cur, tasks)
            logger.info("Populated database and saved output file: %s", dst)
        except Exception as e:
            logger.exception("Failed to populate database from file")
            return repr(e)

        return send_file(
            dst_path.as_posix(),
            as_attachment=True,
            download_name=f"{name}_output.{ext}",
        )
