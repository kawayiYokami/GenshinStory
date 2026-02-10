from dataclasses import dataclass


@dataclass
class RogueMiracle:
    """
    Represents a single Rogue Miracle (奇物) item.
    """
    id: int
    name: str
    description: str