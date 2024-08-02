from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING

from train.models.node import Node, PartialNode

if TYPE_CHECKING:
    from sqlite3 import Cursor

NODE_DATA_PATH = Path.cwd() / "data" / "node.json"


class NodeService:
    @staticmethod
    def init(cur: Cursor) -> None:
        node_raw = json.loads(NODE_DATA_PATH.read_text())
        nodes = [
            PartialNode(name=name, position=position)
            for name, position in product(node_raw, [1, 2])
        ]

        Node.insert_many(cur, nodes)
