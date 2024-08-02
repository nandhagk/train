from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from heapq import heapify, heappop, heappush
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, TypedDict

from result import Err, Ok, Result

from train.db import utcnow
from train.models.slot import PartialSlot, Slot

if TYPE_CHECKING:
    from sqlite3 import Cursor


TRAIN_DATA_PATH = Path.cwd() / "data" / "ARR-RU-DT.json"


class NoFreeSlotError(Exception):
    pass


Interval: TypeAlias = tuple[datetime, datetime]
InsertErr: TypeAlias = NoFreeSlotError


class RawTaskSlotToInsert(TypedDict):
    priority: int

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    task_id: int


@dataclass(frozen=True)
class TaskSlotToInsert:
    priority: int

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    task_id: int

    @staticmethod
    def decode(raw: RawTaskSlotToInsert) -> TaskSlotToInsert:
        return TaskSlotToInsert(**raw)


class SlotService:
    @staticmethod
    def init(cur: Cursor) -> None:
        trains = json.loads(TRAIN_DATA_PATH.read_text())
        trains = {
            tuple(key.split(", ")): SlotService.interpolate(value)
            for key, value in trains.items()
        }

        # pprint(trains)
        # slots = [
        #     PartialSlot(name=name, position=pos)
        #     for name, pos in json.loads(SLOT_DATA_PATH.read_text())
        # ]

        # Slot.insert_many(cur, slots)

    @staticmethod
    def insert_task_slot(
        cur: Cursor,
        section_id: int,
        slot: TaskSlotToInsert,
    ) -> tuple[list[int], list[int]]:
        return SlotService.insert_task_slots(cur, section_id, [slot])

    @staticmethod
    def insert_task_slots(
        cur: Cursor,
        section_id: int,
        slots: list[TaskSlotToInsert],
    ) -> tuple[list[int], list[int]]:
        heapify(slots)

        good_tasks: list[int] = []
        bad_tasks: list[int] = []

        while slots:
            slot = heappop(slots)

            result = SlotService.find_interval_for_task(cur, section_id, slot)
            if isinstance(result, Err):
                bad_tasks.append(slot.task_id)
                continue

            starts_at, ends_at = result.ok()
            intersecting_slots = Slot.pop_intersecting_slots(
                cur,
                section_id,
                starts_at,
                ends_at,
            )

            for intersecting_slot in intersecting_slots:
                heappush(slots, intersecting_slot)

            Slot.insert_one(
                cur,
                PartialSlot(
                    starts_at=starts_at,
                    ends_at=ends_at,
                    priority=slot.priority,
                    section_id=section_id,
                    task_id=slot.task_id,
                    train_id=None,
                ),
            )

            good_tasks.append(slot.task_id)

        return good_tasks, bad_tasks

    @staticmethod
    def find_interval_for_task(
        cur: Cursor,
        section_id: int,
        slot: TaskSlotToInsert,
    ) -> Result[Interval, NoFreeSlotError]:
        fixed_slots = Slot.find_fixed_slots(
            cur,
            section_id=section_id,
            priority=slot.priority,
            after=utcnow() + timedelta(days=1),
        )

        available_free_slots = [
            (before.ends_at, after.starts_at) for before, after in pairwise(fixed_slots)
        ]

        potential_free_slots = [
            (starts_at, ends_at)
            for starts_at, ends_at in available_free_slots
            if starts_at.date() == slot.requested_date
            and ends_at - starts_at >= slot.requested_duration
        ]

        if not potential_free_slots:
            return Err(NoFreeSlotError())

        preferred_starts_at = datetime.combine(
            slot.requested_date,
            slot.preferred_starts_at,
        )

        preferred_ends_at = datetime.combine(
            slot.requested_date,
            slot.preferred_ends_at,
        )

        # Wrap around to next day
        if preferred_ends_at < preferred_starts_at:
            preferred_ends_at += timedelta(days=1)

        def key(interval: tuple[datetime, datetime]) -> timedelta:
            starts_at, ends_at = interval
            return min(ends_at, preferred_ends_at) - max(starts_at, preferred_starts_at)

        slot_starts_at, slot_ends_at = max(potential_free_slots, key=key)

        if slot_starts_at <= preferred_starts_at and preferred_ends_at <= slot_ends_at:
            starts_at = preferred_starts_at
        elif slot_starts_at >= preferred_starts_at:
            starts_at = slot_starts_at
        else:
            starts_at = min(slot_ends_at - slot.requested_duration, preferred_starts_at)

        ends_at = starts_at + slot.requested_duration

        return Ok((starts_at, ends_at))

    @staticmethod
    def interpolate(train): ...
