from __future__ import annotations

from datetime import datetime, time, timedelta
import json
from pathlib import Path
from typing import TYPE_CHECKING

from train.models.train import PartialTrain, Train

if TYPE_CHECKING:
    from sqlite3 import Cursor

TRAIN_INFO_DATA_PATH = Path.cwd() / "data" / "trains_arr_ru.json"
TRAIN_SCHEDULE_DATA_PATH = Path.cwd() / "data" / "ARR-RU-DT.json"


class TrainService:
    @staticmethod
    def init(cur: Cursor) -> None:
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

        print(list(trains.values())[0])

    @staticmethod
    def interpolate_schedule(schedule: dict):
        station_names = list(schedule.keys())
        
        # We assume that if any of arrival or departure is none, set it to the other

        flattened: list[datetime | None] = []
        for station_timing in schedule.values():
            station_timing["arrival"] = station_timing["arrival"] if station_timing["arrival"] is not None else station_timing["departure"]
            station_timing["departure"] = station_timing["departure"] if station_timing["departure"] is not None else station_timing["arrival"]

            flattened.append(
                datetime.combine(
                    datetime(1, 1, 1),
                    time.fromisoformat(station_timing["arrival"])
                )  if station_timing["arrival"] is not None else None
            )
            flattened.append(
                datetime.combine(
                    datetime(1, 1, 1),
                    time.fromisoformat(station_timing["departure"])
                )  if station_timing["departure"] is not None else None
            )

        def fill_between(left: int, right: int):
            start_datetime = flattened[left + 1]
            end_datetime = flattened[right] + timedelta(days=start_datetime > flattened[right])
            
            interpolation_delta = (end_datetime - start_datetime) / (((right - left) // 2))
            interpoled_value = start_datetime + interpolation_delta

            for i in range(left + 2, right, 2):
                flattened[i] = interpoled_value.replace(1, 1, 1)
                flattened[i + 1] = interpoled_value.replace(1, 1, 1)

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
                "arrival": flattened[2*i].time(),
                "departure": flattened[2*i + 1].time()
            } if flattened[2*i] is not None else None
            for i in range(len(station_names))
        }
