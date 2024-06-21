def skipper(raw: str):
    pass

def parser(raw: str):
    raw = raw.strip().upper()
    if (not raw.endswith("YD")) and (not raw.endswith("YD")) and raw.count("-") == 0:
        if raw.count(" ") == 0:
            return (raw + "YD", raw + "YD")


