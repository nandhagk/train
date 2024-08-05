from itertools import chain, pairwise, product
from pathlib import Path

from asyncpg import Connection
from msgspec.json import decode

from train.models.section import PartialSection, Section
from train.repositories.node import NodeRepository
from train.repositories.section import SectionRepository

NODE_DATA_PATH = Path.cwd() / "data" / "node.json"


class SectionService:
    @staticmethod
    async def init(con: Connection) -> list[Section]:
        nodes = {
            (node.name, node.position): node.id
            for node in await NodeRepository.find_all(con)
        }

        node_raw = decode(NODE_DATA_PATH.read_bytes())
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

        return await SectionRepository.insert_many(con, sections)
