# This shit is tooooo bad
# Just decently give good data na ;-;
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

ROW_LIMIT = 6600

MAP = {"block": 4, "section": 3}

Block = str
Section = tuple[str, str]

T = TypeVar("T", Block, Section)

SkipHandler = Callable[[str], bool]
ParseHandler = Callable[[str], T]
SkipHandlers = list[SkipHandler]
ParseHandlers = list[ParseHandler[T]]


def get_scope(source: str):
    glob = {}
    exec(source, glob)
    return glob


def get_parser(source: str):
    scope = get_scope(source)
    return scope["parser"]


def get_skipper(source: str):
    scope = get_scope(source)
    return scope["skipper"]


def load_source(
    path: Path,
) -> tuple[list[str], dict[str, T], tuple[list[str], list[str]]]:
    dat = json.loads(path.read_text())
    return (dat["skiplist"], dat["acceptor"], dat["handlers"])


def dump(skiplist, acceptor, source_code: tuple[list[str], list[str]], path: Path):
    path.write_text(
        json.dumps(
            {"skiplist": skiplist, "acceptor": acceptor, "handlers": source_code},
        ),
    )


def load_handlers(
    source_code: tuple[list[str], list[str]],
) -> tuple[SkipHandlers, ParseHandlers[T]]:
    ret = ([], [])

    for handler_src in source_code[0]:
        ret[0].append(get_skipper(handler_src))
    for handler_src in source_code[1]:
        ret[1].append(get_parser(handler_src))

    return ret


def should_skip(item: str, skip_handlers: SkipHandlers):
    return any(func(item) for func in skip_handlers)


def parse(item: str, parse_handlers: ParseHandlers[T]) -> T | None:
    for handler in parse_handlers:
        if (res := handler(item)) is not None:
            return res
    return None


def main(path: Path, block_source: Path, section_source: Path):
    with open(path.as_posix()) as f:
        reader = csv.reader(f)
        data = [next(reader) for i in range(ROW_LIMIT)]

    block_accepts: dict[str, Block]
    section_accepts: dict[str, Section]
    block_rejects, block_accepts, block_source_code = load_source(block_source)
    section_rejects, section_accepts, section_source_code = load_source(section_source)
    block_handlers: tuple[SkipHandlers, ParseHandlers[Block]] = load_handlers(
        block_source_code,
    )
    section_handlers: tuple[SkipHandlers, ParseHandlers[Section]] = load_handlers(
        section_source_code,
    )

    block_action_file: str = input("Enter file to take BLOCK skipper or parser from: ")
    section_action_file: str = input(
        "Enter file to take SECTION skipper or parser from: ",
    )

    their_section_to_our_section_map: dict[str, Section] = {}

    def _parse_generic(
        item: Any,
        handlers: tuple[SkipHandlers, ParseHandlers[T]],
        source_code: tuple[list[str], list[str]],
        debug_name: str,
        action_file: str,
        acceptor: dict[str, T],
        skiplist: list[str],
    ) -> T | None:
        if not isinstance(item, str):
            return None
        if item in skiplist:
            return None
        if should_skip(item, handlers[0]):
            return None

        if acceptor.get(item) is not None:
            return acceptor[item]

        result = parse(item, handlers[1])
        if result is not None:
            return result

        print(f"Could not handle {debug_name} `{item}`")

        while True:
            command, _, value = input(
                "Please give next action (use / skip / acc / rej): ",
            ).partition(" ")
            if command not in ("use", "skip", "acc", "rej"):
                print("Please give a valid command!")
                continue

            if command == "acc" and not value:
                print("Please provide a value to accept this block as!")
                continue

            break

        if command == "use":
            try:
                source_code[1].append(Path(action_file).read_text())
                handler = get_parser(Path(action_file).read_text())
                if (r := handler(item)) is not None:
                    handlers[1].append(handler)
                    return r
                print("WARNING! Handler could not handle the data lmao")

            except Exception as e:
                print(e, file=sys.stderr)

        elif command == "skip":
            try:
                source_code[0].append(Path(action_file).read_text())
                handler = get_skipper(Path(action_file).read_text())
                if (r := handler(item)) is not None:
                    handlers[0].append(handler)
                    return r
                print("WARNING! Handler could not handle the data lmao")

            except Exception as e:
                print(e, file=sys.stderr)

        elif command == "acc":
            acceptor[item] = eval(value)

        elif command == "rej":
            skiplist.append(item)

        return _parse_generic(
            item,
            handlers,
            source_code,
            debug_name,
            action_file,
            acceptor,
            skiplist,
        )

    def parse_block_name(block_name: Any) -> str | None:
        return _parse_generic(
            block_name,
            block_handlers,
            block_source_code,
            "block",
            block_action_file,
            block_accepts,
            block_rejects,
        )

    def parse_section_name(section_name: Any) -> tuple[str, str] | None:
        return _parse_generic(
            section_name,
            section_handlers,
            section_source_code,
            "section",
            section_action_file,
            section_accepts,
            section_rejects,
        )

    mas = defaultdict(list)

    for row in range(ROW_LIMIT):
        print(row)

        section_name = data[row][MAP["section"]]
        block_name = data[row][MAP["block"]]

        block = parse_block_name(block_name)
        section = parse_section_name(section_name) if block is not None else None
        if section is not None:
            their_section_to_our_section_map[section_name] = section

        if block is None or section is None:
            print("IGNORING ROW!", row, f"`{block_name}`, `{section_name}`")
            continue

        mas[block].append(list(section))

    dump(block_rejects, block_accepts, block_source_code, block_source)
    dump(section_rejects, section_accepts, section_source_code, section_source)
    Path("mas2.json").write_text(json.dumps(mas))
    Path("masection.json").write_text(json.dumps(their_section_to_our_section_map))

    return 0


if __name__ == "__main__":

    sys.exit(
        main(
            Path(
                sys.argv[1] if len(sys.argv) > 1 else "SR_Rolling_Block_Programme.csv",
            ),
            Path(sys.argv[2] if len(sys.argv) > 2 else "block_handlers.json"),
            Path(sys.argv[3] if len(sys.argv) > 3 else "section_handlers.json"),
        ),
    )
