from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from logging import getLogger
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, request, send_file
from flask.logging import create_logger
from result import Err

from train.db import get_db
from train.file_management import FileManager
from train.models.task import PartialTask, Task

from zipfile import ZipFile

logger = getLogger(__name__)
app = Flask("app")

@app.get("/")
def home():
    """Return html."""
    return send_file((Path.cwd() / "client" / "index.html").as_posix())


@app.post("/request")
def handle_form():
    """Handle form."""
    f = request.files["fileInput"]
    assert f.filename is not None

    name, _, ext = f.filename.rpartition(".")

        
    src_path = (Path.cwd() / "tmp" / os.urandom(24).hex()).with_suffix("." + ext)
    dst_path = (Path.cwd() / "tmp" / os.urandom(24).hex()).with_suffix("." + ext)
    err_path = (Path.cwd() / "tmp" / os.urandom(24).hex()).with_suffix("." + ext)

    def clean():
        if src_path.is_file(): src_path.unlink()
        if dst_path.is_file(): dst_path.unlink()
        if err_path.is_file(): err_path.unlink()

    f.save(src_path.as_posix())

    con = get_db()
    cur = con.cursor()

    try:
        taskqs_per_section: dict[int, list[tuple[PartialTask, int]]] = defaultdict(list)
        skipped_data: list[tuple[int, str]] = []

        fm = FileManager.get_manager(src_path, dst_path, err_path)
        for idx, res in enumerate(fm.read(cur)):
            if isinstance(res, Err):
                skipped_data.append((idx + 1, res.err_value))
                continue
            taskq = res.value
            taskqs_per_section[taskq.section_id].append((taskq, idx + 1))

        tasks: list[Task] = []
        for section_id, rows in taskqs_per_section.items():
            logger.info("Scheduling %d", section_id)

            res = Task.insert_many(cur, [taskq for taskq, _idx in rows])
            if isinstance(res, Err):
                logger.warning("Ignoring %d", section_id, exc_info=res.err_value)
                skipped_data.extend((idx, repr(res.err_value)) for _taskq, idx in rows)
            else:
                tasks.extend(res.value)

        fm.write(cur, tasks)
        fm.write_error(skipped_data)
        logger.info("Populated database and saved output file: %s", dst_path.name)
    except Exception as e:
        logger.exception("Failed to populate database from file")
        clean()
        return repr(e)
    
    stream = BytesIO()
    with ZipFile(stream, 'w') as zf:
        zf.write(dst_path, f"{name}_output.{ext}")
        zf.write(err_path, f"{name}_errors.{ext}")

    stream.seek(0)

    clean()
    return send_file(
        stream,
        as_attachment=True,
        download_name='archive.zip'
    )
