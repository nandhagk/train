def skipper(raw: str):
    pass


def parser(raw: str):
    raw, _, _ = raw.partition("/")
    raw = raw.strip().replace("-", " ").replace("_", " ").upper()
    yard_endings = ["YD", "YARD", "Y D"]
    for ed in yard_endings:
        if raw.endswith(ed):
            raw = raw.removesuffix(ed).strip()
            if raw.count(" ") == 0:
                return raw + " YD", raw + " YD"
    return None
