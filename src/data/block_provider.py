def skipper(raw: str):
    pass


def parser(raw: str):
    raw = raw.strip()
    a, _, b = raw.partition("-")
    a = a.strip().replace("-", " ").replace("_", " ")
    b = b.strip().replace("-", " ").replace("_", " ")
    _ = _.strip()

    if not _ or not b:
        return None

    if a.count(" ") == 0 and b.count(" ") == 0:
        return a.upper() + "-" + b.upper()
    return None
