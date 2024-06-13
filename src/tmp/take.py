def handler(raw: str):
    
    if raw == "MLPM": return [raw, raw]


def fix():
    import json
    from pathlib import Path
    dp = Path(__file__).with_name("mas.json")
    data = json.loads(dp.read_text())

    for block in data:
        for i in range(len(data[block])):
            if type(data[block][i]) == str:
                data[block][i] = [data[block][i], data[block][i]]
    dp.write_text(json.dumps(data))

if __name__ == '__main__':
    # fix()
    pass