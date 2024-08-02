from __future__ import annotations

from datetime import date, datetime, time, timedelta
from functools import lru_cache
from itertools import pairwise
import json
from pathlib import Path

from typing import TYPE_CHECKING, cast

from train.db import combine
from train.models.section import Section
from train.models.slot import Slot, PartialSlot
from train.models.train import PartialTrain, Train

if TYPE_CHECKING:
    from sqlite3 import Cursor

TRAIN_INFO_DATA_PATH = Path.cwd() / "data" / "trains_arr_ru.json"
TRAIN_SCHEDULE_DATA_PATH = Path.cwd() / "data" / "train.json"

TRAIN_SLOT_FILL_LENGTH = 380
TRAIN_PRIORITY = 1_000_000

class TrainService:
    @staticmethod
    def init(cur: Cursor) -> None:
        @lru_cache
        def find_section(start: str, end: str, line: str):
            return Section.find_by_node_name(cur, start, end, line)

        trains = [
            PartialTrain(name=data["name"], number=data["number"])
            for data in json.loads(TRAIN_INFO_DATA_PATH.read_text())
        ]

        Train.insert_many(cur, trains)

        trains = json.loads(TRAIN_SCHEDULE_DATA_PATH.read_text())
        trains = {
            tuple(key.split(", ")): value
            for key, value in trains.items()
        }

        for line in ("UP",):
            for train_data, stations in trains.items():
                # get train_id
                number, on_days = train_data
                assert len(on_days) == 7

                train = Train.find_by_number(cur, number)
                assert train is not None

                for i in range(TRAIN_SLOT_FILL_LENGTH):
                    date = datetime.today() + timedelta(days=i)
                    if on_days[date.weekday()] == '0': 
                        continue

                    for a, b in pairwise(stations.keys()):
                        section = find_section(a, b, line)
                        assert section is not None

                        starts_at = combine(date, time.fromisoformat(stations[a]['departure']))
                        ends_at = combine(date, time.fromisoformat(stations[b]['arrival']))
                        if starts_at > ends_at:
                            ends_at += timedelta(days=1)

                        Slot.insert_one(cur, PartialSlot(starts_at=starts_at, ends_at=ends_at, section_id=section.id, priority=TRAIN_PRIORITY, train_id=train.id, task_id=None))