from datetime import date, datetime, time, timedelta
from functools import cached_property
from heapq import heapify, heappop, heappush
from itertools import pairwise
from typing import Self, TypeAlias

from asyncpg import Connection, Record
from msgspec import Struct

from train.models.slot import PartialSlot
from train.repositories.slot import SlotRepository
from train.utils import combine, now, timediff


class NoFreeSlotError(Exception):
    pass


Interval: TypeAlias = tuple[datetime, datetime]
InsertErr: TypeAlias = NoFreeSlotError


class TaskSlotToInsert(Struct, frozen=True, kw_only=True):
    priority: int
    task_id: int

    preferred_starts_at: time
    preferred_ends_at: time

    requested_date: date
    requested_duration: timedelta

    @classmethod
    def decode(cls, row: Record) -> Self:
        return cls(**row)

    @cached_property
    def preferred_range(self):
        return timediff(self.preferred_starts_at, self.preferred_ends_at)

    def __lt__(self, other: Self) -> bool:
        if self.priority != other.priority:
            return self.priority > other.priority

        if self.requested_duration != other.requested_duration:
            return self.requested_duration > other.requested_duration

        if self.preferred_range != other.preferred_range:
            return self.preferred_range < other.preferred_range

        return self.preferred_starts_at < other.preferred_starts_at


class SlotService:
    @staticmethod
    async def insert_task_slot(
        con: Connection,
        section_id: int,
        slot: TaskSlotToInsert,
    ) -> tuple[list[int], list[int]]:
        return await SlotService.insert_task_slots(con, section_id, [slot])

    @staticmethod
    async def insert_task_slots(
        con: Connection,
        section_id: int,
        slots: list[TaskSlotToInsert],
    ) -> tuple[list[int], list[int]]:
        heapify(slots)

        good_tasks: list[int] = []
        bad_tasks: list[int] = []

        while slots:
            slot = heappop(slots)

            try:
                starts_at, ends_at = await SlotService.find_interval_for_task(
                    con,
                    section_id,
                    slot,
                )
            except NoFreeSlotError:
                bad_tasks.append(slot.task_id)
                continue

            intersecting_slots = await SlotRepository.pop_intersecting(
                con,
                priority=slot.priority,
                section_id=section_id,
                starts_at=starts_at,
                ends_at=ends_at,
            )

            for intersecting_slot in intersecting_slots:
                heappush(slots, intersecting_slot)

            await SlotRepository.insert_one(
                con,
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
    async def find_interval_for_task(
        con: Connection,
        section_id: int,
        slot: TaskSlotToInsert,
    ) -> Interval:
        fixed_slots = await SlotRepository.find_fixed(
            con,
            section_id=section_id,
            priority=slot.priority,
            after=now() + timedelta(days=1),
        )

        available_free_slots = [
            (before.ends_at, after.starts_at) for before, after in pairwise(fixed_slots)
        ]

        potential_free_slots = [
            (starts_at, ends_at)
            for starts_at, ends_at in available_free_slots
            if starts_at.date() <= slot.requested_date <= ends_at.date()
            and ends_at - starts_at >= slot.requested_duration
        ]
        if not potential_free_slots:
            raise NoFreeSlotError

        preferred_starts_at = combine(
            slot.requested_date,
            slot.preferred_starts_at,
        )

        preferred_ends_at = combine(
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
        return starts_at, ends_at
