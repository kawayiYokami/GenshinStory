from dataclasses import dataclass


@dataclass
class RogueMagicScepter:
    """
    Represents a single Rogue Magic Scepter (奇物) item.
    """
    id: int
    name: str
    description: str
    trigger_desc: str