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
TRAIN_SCHEDULE_DATA_PATH = Path.cwd() / "data" / "ARR-RU-DT.json"

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
            tuple(key.split(", ")): TrainService.interpolate_schedule(value)
            for key, value in trains.items()
        }

        for line in ("UP",):
            for train_data, stations in trains.items():
                # get train_id
                train = Train.find_by_number(cur, train_data[0])
                if train is None:
                    print(train_data)
                assert train is not None

                on_days = train_data[1]
                assert len(on_days) == 7

                for date in (datetime.today() + timedelta(days=i) for i in range(TRAIN_SLOT_FILL_LENGTH)):
                    if on_days[date.weekday()] == '0': continue
                    for a, b in pairwise(stations.keys()):
                        section = find_section(a, b, line)
                        if section is None:
                            print(a, b, line)
                        assert section is not None

                        starts_at = combine(date, stations[a]['departure'])
                        ends_at = combine(date, stations[b]['arrival'])

                        ends_at += timedelta(days = starts_at > ends_at)
                        Slot.insert_one(cur, PartialSlot(starts_at=starts_at, ends_at=ends_at, section_id=section.id, priority=TRAIN_PRIORITY, train_id=train.id, task_id=None))



    @staticmethod
    def interpolate_schedule(schedule: dict):
        station_names = list(schedule.keys())
        
        # We assume that if any of arrival or departure is none, set it to the other

        flattened: list[datetime | None] = []
        for station_timing in schedule.values():
            station_timing["arrival"] = station_timing["arrival"] if station_timing["arrival"] is not None else station_timing["departure"]
            station_timing["departure"] = station_timing["departure"] if station_timing["departure"] is not None else station_timing["arrival"]

            flattened.append(
                combine(
                    date.min,
                    time.fromisoformat(station_timing["arrival"])
                )  if station_timing["arrival"] is not None else None
            )
            flattened.append(
                combine(
                    date.min,
                    time.fromisoformat(station_timing["departure"])
                )  if station_timing["departure"] is not None else None
            )

        def fill_between(left: int, right: int):
            start_datetime = flattened[left + 1]
            end_datetime = flattened[right]
            assert start_datetime is not None and end_datetime is not None
            end_datetime = end_datetime + timedelta(days=start_datetime > end_datetime)
            
            interpolation_delta = (end_datetime - start_datetime) / (((right - left) // 2))
            interpoled_value = start_datetime + interpolation_delta

            for i in range(left + 2, right, 2):
                flattened[i] = combine(date.min, interpoled_value.time())
                flattened[i + 1] = combine(date.min, interpoled_value.time())

                interpoled_value += interpolation_delta
                # Linearly interplotate values of arrival
                # Set arrival and departure to the same

        l = 0
        while l < (len(flattened)) and flattened[l] == None: l += 2

        r = l + 2
        while r < (len(flattened)) and flattened[r] == None: r += 2
        
        while r < len(flattened):
            fill_between(l, r)
            l = r
            r += 2
            
            while r < (len(flattened)) and flattened[r] == None: r += 2
        
        return {
            station_names[i]: {
                "arrival": cast(datetime, flattened[2*i]).time(),
                "departure": cast(datetime, flattened[2*i + 1]).time()
            }
            for i in range(len(station_names))
            if flattened[2*i] is not None
        }
