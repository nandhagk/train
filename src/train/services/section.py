from __future__ import annotations

import json
from itertools import chain, pairwise, product
from pathlib import Path
from typing import TYPE_CHECKING

from train.models.node import Node
from train.models.section import PartialSection, Section

if TYPE_CHECKING:
    from sqlite3 import Cursor

NODE_DATA_PATH = Path.cwd() / "data" / "node.json"


class SectionService:
    @staticmethod
    def init(cur: Cursor) -> None:
        nodes = {(node.name, node.position): node.id for node in Node.find_many(cur)}

        node_raw = json.loads(NODE_DATA_PATH.read_text())
        node_ids = [nodes[key] for key in product(node_raw, [1, 2])]

        sections = chain(
            (
                PartialSection(line="UP", from_id=start, to_id=end)
                for start, end in pairwise(node_ids)
            ),
            (
                PartialSection(line="DN", from_id=start, to_id=end)
                for start, end in pairwise(reversed(node_ids))
            ),
        )

        Section.insert_many(cur, sections)
