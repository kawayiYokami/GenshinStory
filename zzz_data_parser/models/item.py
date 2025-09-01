from dataclasses import dataclass


@dataclass
class Item:
    """
    Represents a game item with its associated data.
    """
    id: int
    """The unique numerical identifier for the item."""

    name: str = ""
    """The name of the item."""

    description: str = ""
    """The functional description of the item."""

    story: str = ""
    """The background story or lore of the item."""