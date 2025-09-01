from dataclasses import dataclass


@dataclass
class HollowItem:
    """
    Represents a Hollow (Roguelike) item with its associated data.
    """
    id: int
    """The unique numerical identifier for the hollow item."""

    name: str = ""
    """The name of the hollow item."""

    description: str = ""
    """The description of the hollow item."""