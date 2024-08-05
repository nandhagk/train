from itertools import product
from pathlib import Path

from asyncpg import Connection
from msgspec.json import decode

from train.models.node import Node, PartialNode
from train.repositories.node import NodeRepository

NODE_DATA_PATH = Path.cwd() / "data" / "node.json"


class NodeService:
    @staticmethod
    async def init(con: Connection) -> list[Node]:
        node_raw = decode(NODE_DATA_PATH.read_bytes())
        nodes = [
            PartialNode(name=name, position=position)
            for name, position in product(node_raw, [1, 2])
        ]

        return await NodeRepository.insert_many(con, nodes)
