from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import cast

TRAIN_SCHEDULE_DATA_PATH = Path.cwd() / "ARR-RU-DT.json"
TRAIN_SCHEDULE_INTERPOL_DATA_PATH = Path.cwd() / "train.json"


def interpol() -> None:
    trains = json.loads(TRAIN_SCHEDULE_DATA_PATH.read_text())
    trains = {key: interpolate_schedule(value) for key, value in trains.items()}

    with TRAIN_SCHEDULE_INTERPOL_DATA_PATH.open("w") as f:
        f.write(json.dumps(trains, indent=2))


def interpolate_schedule(schedule: dict):
    station_names = list(schedule.keys())

    # TODO:
    # We assume that if any of arrival or departure is none, set it to the other

    flattened: list[datetime | None] = []
    for station_timing in schedule.values():
        station_timing["arrival"] = (
            station_timing["arrival"]
            if station_timing["arrival"] is not None
            else station_timing["departure"]
        )
        station_timing["departure"] = (
            station_timing["departure"]
            if station_timing["departure"] is not None
            else station_timing["arrival"]
        )

        flattened.append(
            datetime.combine(date.min, time.fromisoformat(station_timing["arrival"]))
            if station_timing["arrival"] is not None
            else None
        )
        flattened.append(
            datetime.combine(date.min, time.fromisoformat(station_timing["departure"]))
            if station_timing["departure"] is not None
            else None
        )

    def fill_between(left: int, right: int):
        start_datetime = flattened[left + 1]
        end_datetime = flattened[right]
        assert start_datetime is not None
        assert end_datetime is not None
        end_datetime = end_datetime + timedelta(days=start_datetime > end_datetime)

        interpolation_delta = (end_datetime - start_datetime) / ((right - left) // 2)
        interpoled_value = start_datetime + interpolation_delta

        for i in range(left + 2, right, 2):
            flattened[i] = datetime.combine(date.min, interpoled_value.time())
            flattened[i + 1] = datetime.combine(date.min, interpoled_value.time())

            interpoled_value += interpolation_delta
            # Linearly interplotate values of arrival
            # Set arrival and departure to the same

    l = 0
    while l < len(flattened) and flattened[l] is None:
        l += 2

    r = l + 2
    while r < len(flattened) and flattened[r] is None:
        r += 2

    while r < len(flattened):
        fill_between(l, r)
        l = r
        r += 2

        while r < len(flattened) and flattened[r] is None:
            r += 2

    return {
        station_names[i]: {
            "arrival": cast(datetime, flattened[2 * i]).time().isoformat(),
            "departure": cast(datetime, flattened[2 * i + 1]).time().isoformat(),
        }
        for i in range(len(station_names))
        if flattened[2 * i] is not None
    }


if __name__ == "__main__":
    interpol()
