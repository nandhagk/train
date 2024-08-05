from datetime import time, timedelta
from itertools import pairwise
from pathlib import Path

from asyncpg import Connection
from msgspec.json import decode

from train.models.section import Section
from train.models.slot import PartialSlot
from train.models.train import PartialTrain, Train
from train.repositories.section import SectionRepository
from train.repositories.slot import SlotRepository
from train.repositories.train import TrainRepository
from train.utils import combine, now

TRAIN_INFO_DATA_PATH = Path.cwd() / "data" / "trains_arr_ru.json"
TRAIN_SCHEDULE_DATA_PATH = Path.cwd() / "data" / "train.json"

TRAIN_SLOT_FILL_LENGTH = 380
TRAIN_PRIORITY = 1_000_000


class TrainService:
    @staticmethod
    async def init(con: Connection) -> list[Train]:
        _cache: dict[tuple[str, str, str], Section] = {}

        async def find_section(line: str, start: str, end: str) -> Section:
            key = (line, start, end)
            try:
                return _cache[key]
            except KeyError:
                section = await SectionRepository.find_one_by_line_and_names(
                    con,
                    line,
                    start,
                    end,
                )
                assert section is not None

                _cache[key] = section
                return section

        trains = [
            PartialTrain(name=data["name"], number=data["number"])
            for data in decode(TRAIN_INFO_DATA_PATH.read_text())
        ]

        created_trains = await TrainRepository.insert_many(con, trains)
        created_trains = {train.number: train for train in created_trains}

        trains = decode(TRAIN_SCHEDULE_DATA_PATH.read_text())
        trains = {tuple(key.split(", ")): value for key, value in trains.items()}

        slots: list[PartialSlot] = []
        for line in ("UP",):
            for train_data, stations in trains.items():
                # get train_id
                number, on_days = train_data
                assert len(on_days) == 7  # noqa: PLR2004

                train = created_trains[number]
                assert train is not None

                for i in range(TRAIN_SLOT_FILL_LENGTH):
                    date = now().date() + timedelta(days=i)
                    if on_days[date.weekday()] == "0":
                        continue

                    for a, b in pairwise(stations.keys()):
                        section = await find_section(line, a, b)

                        starts_at = combine(
                            date,
                            time.fromisoformat(stations[a]["departure"]),
                        )
                        ends_at = combine(
                            date,
                            time.fromisoformat(stations[b]["arrival"]),
                        )
                        if starts_at > ends_at:
                            ends_at += timedelta(days=1)

                        slots.append(
                            PartialSlot(
                                starts_at=starts_at,
                                ends_at=ends_at,
                                section_id=section.id,
                                priority=TRAIN_PRIORITY,
                                train_id=train.id,
                                task_id=None,
                            ),
                        )

        await SlotRepository.insert_many(con, slots)
        return list(created_trains.values())
