def skipper(raw: str):
    pass

def parser(raw: str):
    raw = raw.strip().upper()
    raw = raw.replace("-", " ").replace("_", " ")
    if raw.endswith("YD"):
        raw = raw.removesuffix("YD").strip()
        if raw.count(" ") == 0:
            return raw
        
    

