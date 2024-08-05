import json


def time_to_minutes(time_str):
    """Convert HH:MM time string to minutes since midnight."""
    if time_str is None:
        return None
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def find_corridor_blocks(data):
    blocks = []

    for key, stations in data.items():
        last_departure_time = None
        last_station = None
        for station, times in stations.items():
            arrival = time_to_minutes(times["arrival"])
            departure = time_to_minutes(times["departure"])

            if departure is not None:
                assert arrival is not None
                if last_departure_time is not None and last_departure_time < arrival:
                    # There is a corridor block
                    blocks.append(
                        {
                            "corridor": (last_station, station),
                            "start_time": last_departure_time,
                            "end_time": arrival,
                        }
                    )

            last_station = station
            last_departure_time = departure

    return blocks


def format_time(minutes):
    """Convert minutes since midnight to HH:MM time string."""
    if minutes is None:
        return None
    h = minutes // 60
    m = minutes % 60
    return f"{h:02}:{m:02}"


def main():
    # Load JSON data
    with open("ARR-RU.json") as f:
        data = json.load(f)

    # Find corridor blocks
    corridor_blocks = find_corridor_blocks(data)

    # Prepare the output for JSON file
    output = []
    for block in corridor_blocks:
        output.append(
            {
                "corridor": block["corridor"],
                "start_time": format_time(block["start_time"]),
                "end_time": format_time(block["end_time"]),
            }
        )

    # Write to JSON file
    with open("corridor_block.json", "w") as f:
        json.dump(output, f, indent=4)


if __name__ == "__main__":
    main()
