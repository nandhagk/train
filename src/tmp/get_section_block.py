from ast import Call
import sys
from pathlib import Path
from typing import Callable, final

StationName = str
BlockName = str
Section = tuple[StationName, StationName]

def remove_duplicate_space(raw: str):
    return ' '.join(raw.split())


def main(file: Path):
    data = file.read_text().splitlines()
    blocks: dict[BlockName, list[Section]] = {

    }

    rblock_handlers: list[str] = []
    rsection_handlers: list[str] = []

    block_handlers: list[Callable[[str], BlockName | None]] = [

    ]

    section_handlers: list[Callable[[str], Section | None]] = [

    ]

    def get_block_name(raw: str):
        for handler in block_handlers:
            if (result := handler(raw)) is not None: return result

        new_handler = input(f"Enter block handler for `{raw}`: ")
        if new_handler == '': return None

        from runpy import run_path
        try:
            rblock_handlers.append(Path(new_handler).read_text())
            result = run_path(new_handler)
            handler = result['handler']
            if (r := handler(raw)) is not None:
                block_handlers.append(handler)
                return r
            print("WARNING! Handler could not handle the data lmao")

        except Exception as e:
            print(e, file=sys.stderr)
        finally:
            return get_block_name(raw)

    def get_section(raw: str):
        for handler in section_handlers:
            if (result := handler(raw)) is not None: return result

        new_handler = input(f"Enter section handler for `{raw}`: ")
        if new_handler == '': return None

        from runpy import run_path
        try:
            result = run_path(new_handler)
            rsection_handlers.append(Path(new_handler).read_text())
            handler = result['handler']
            if (r := handler(raw)) is not None:
                section_handlers.append(handler)
                return r
            print("WARNING! Handler could not handle the data lmao")

        except Exception as e:
            print(e, file=sys.stderr)
        finally:
            return get_section(raw)

    for line in data:
        # print(data)
        # print(line)
        rsection, rblock = line.strip().split(",")

        block_name = get_block_name(remove_duplicate_space(rblock))
        if block_name == None: continue

        section = get_section(remove_duplicate_space(rsection))
        if section == None: continue
        
        if blocks.get(block_name) is None: blocks[block_name] = []
        blocks[block_name].append(section)

    from json import dump
    with open(file.with_suffix(".json").as_posix(), 'w') as f:
        dump(blocks, f)
    with open(file.with_suffix(".bhandlers.json").as_posix(), 'w') as f:
        dump(rblock_handlers, f)
    with open(file.with_suffix(".shandlers.json").as_posix(), 'w') as f:
        dump(rsection_handlers, f)

    return 0




if __name__ == '__main__':
    file = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    if not file.is_file():
        print("ERROR! Provide valid data file", file=sys.stderr)
        exit(1)

    exit(main(file))