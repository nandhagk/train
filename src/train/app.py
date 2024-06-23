from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from zipfile import ZipFile

from flask import Flask, Response, g, request, send_file
from result import Err

from train.db import get_db
from train.file_management import FileManager
from train.models.task import PartialTask, Task

logger = getLogger(__name__)
app = Flask("app")


def get_db_():  # noqa: D103
    if "db" not in g:
        g.db = get_db()

    return g.db


def close_db(_e=None):  # noqa: D103, ANN001
    db = g.pop("db", None)

    if db is not None:
        db.close()


app.teardown_appcontext(close_db)


@app.get("/")
def home():
    """Return html."""
    return send_file((Path.cwd() / "client" / "index.html").as_posix())


lock = Lock()


@app.post("/request")
def handle_form():
    """Handle form."""
    with lock:
        f = request.files["fileInput"]
        assert f.filename is not None

        name, _, ext = f.filename.rpartition(".")

        with (
            NamedTemporaryFile(suffix=f".{ext}", delete_on_close=False) as src,
            NamedTemporaryFile(suffix=f".{ext}", delete_on_close=False) as dst,
            NamedTemporaryFile(suffix=f".{ext}", delete_on_close=False) as err,
        ):
            src_path = Path(src.name)
            dst_path = Path(dst.name)
            err_path = Path(err.name)

            f.save(src_path.as_posix())

            con = get_db_()
            cur = con.cursor()

            try:
                taskqs_per_section: dict[int, list[tuple[PartialTask, int]]] = (
                    defaultdict(
                        list,
                    )
                )
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
                        logger.warning(
                            "Ignoring %d",
                            section_id,
                            exc_info=res.err_value,
                        )
                        skipped_data.extend(
                            (idx, repr(res.err_value)) for _taskq, idx in rows
                        )
                    else:
                        tasks.extend(res.value)

                fm.write(cur, tasks)
                fm.write_error(skipped_data)
                logger.info(
                    "Populated database and saved output file: %s",
                    dst_path.name,
                )
            except Exception as e:
                logger.exception("Failed to populate database from file")
                return Response(repr(e), 400)

            stream = BytesIO()
            with ZipFile(stream, "w") as zf:
                zf.write(dst_path, f"{name}_output.{ext}")
                zf.write(err_path, f"{name}_errors.{ext}")

            stream.seek(0)

        return send_file(
            stream,
            as_attachment=True,
            download_name="archive.zip",
        )
