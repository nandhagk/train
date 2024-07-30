from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from train.models.train import PartialTrain, Train

if TYPE_CHECKING:
    from sqlite3 import Cursor

TRAIN_DATA_PATH = Path.cwd() / "data" / "trains_arr_ru.json"


class TrainService:
    @staticmethod
    def init(cur: Cursor) -> None:
        trains = [
            PartialTrain(name=data["name"], number=data["number"])
            for data in json.loads(TRAIN_DATA_PATH.read_text())
        ]

        Train.insert_many(cur, trains)
