from datetime import timedelta
from typing import cast

from .format import Format, ParseHelper, Standard


class MASFormat(Format):
    @staticmethod
    def convert_from_standard(standard: Standard) -> dict:
        return {
            "DATE": standard["date"].isoformat(),
            "Department": standard["department"],
            "DEN": standard["den"],
            "Block Section/ Yard": standard["block_section_or_yard"],
            "CORRIDOR block section": standard["corridor_block"],
            # # "corridor block period",
            "UP/ DN Line": standard["line"],
            # # "Block demanded in Hrs(Day or Night)",
            "Demanded time (From)": standard["demanded_time_from"].isoformat(),
            "Demanded time (To)": standard["demanded_time_to"].isoformat(),
            "Block demanded in(MINS)": (
                round(standard["block_demanded"].total_seconds() / 60)
            ),
            "Permitted time (From) No need to fill": (
                standard["permitted_time_from"].isoformat()
                if standard["permitted_time_from"] is not None
                else None
            ),
            "Permitted time (To) No need to fill": (
                standard["permitted_time_to"].isoformat()
                if standard["permitted_time_to"] is not None
                else None
            ),
            "BLOCK PERMITTED MINS": (
                (round(standard["block_permitted"].total_seconds() / 60))
                if standard["block_permitted"] is not None
                else 0
            ),
            # # "Location - FROM",
            # # "Location - TO",
            "Nautre of work & Quantum of Output Planned": standard["nature_of_work"],
            # # "Need for disconnection (If Yes Track Circuit and Signals Affected) Please give specific details without fail",  # noqa: E501
            # # "Caution required",
            # # "Caution required (if yes with relaxation date dd:mm:yyyy)",
            # # "Power Block & its Elementary Section. Please give specific details without fail",  # noqa: E501
            # # "Resources needed (M/C, Manpower, Supervisors) Include Crane,JCB,porcelain or any other equipment also",  # noqa: E501
            # # "Whether site preparation & resources ready",
            # # "Supervisors to be deputed (JE/SSE with section)",
            # # "Coaching repercussions/ Movement Repercussions",
            # "Actual Block Granted From No need to fill": standard["actual_block_from"]
            # "Actual Block Granted To No need to fill": standard["actual_block_to"],
            # "Actual block duration MINS No need to fill": standard["block_actual"],
            # "Over all % granted for the day No need to fill": standard["overall_per"],
            # "Output as per Manual No need to fill": standard["output"],
            # "Actual Output",
            # "% Output vs Planned\nNo need to fill",
            # # "% Output\nvs\nPlanned",
            # # "PROGRESS",
            "LOCATION": standard["location"],
            # "SECTION",
            # "ARB/RB",
        }

    @staticmethod
    def convert_to_standard(data: dict) -> Standard:
        """Can raise either `KeyError` or `ValueError`."""
        mapped = {
            "priority": 1,
            "date": ParseHelper.get_date(data["DATE"]),
            "block_section_or_yard": data["Block Section/ Yard"],
            "corridor_block": data["CORRIDOR block section"],
            "line": data["UP/ DN Line"],
            "demanded_time_from": ParseHelper.get_time(data["Demanded time (From)"]),
            "demanded_time_to": ParseHelper.get_time(data["Demanded time (To)"]),
            "block_demanded": timedelta(
                minutes=ParseHelper.get_int(data["Block demanded in(MINS)"]),
            ),
            "permitted_time_from": ParseHelper.get_time(
                data["Permitted time (From) No need to fill"],
            ),
            "permitted_time_to": ParseHelper.get_time(
                data["Permitted time (To) No need to fill"],
            ),
            "block_permitted": timedelta(
                minutes=ParseHelper.get_int(data["BLOCK PERMITTED MINS"]),
            ),
            "department": data["Department"],
            "den": data["DEN"],
            "nature_of_work": data["Nautre of work & Quantum of Output Planned"],
            "location": data["LOCATION"],
        }

        for name in (
            "block_section_or_yard",
            "corridor_block",
            "line",
            "department",
            "den",
            "nature_of_work",
            "location",
        ):
            if not isinstance(mapped[name], str):
                msg = f"Invalid data! The data does not contain valid type for `{name}`"
                raise ValueError(msg)  # noqa: TRY004

        for name in (
            "date",
            "demanded_time_from",
            "demanded_time_to",
            "block_demanded",
        ):
            if mapped[name] is None:
                msg = f"Invalid data! The data does not contain valid type for `{name}`"
                raise ValueError(msg)

        return cast(Standard, mapped)
