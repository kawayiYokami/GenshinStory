from dataclasses import dataclass


@dataclass
class VHSCollection:
    """
    Represents a VHS Collection item with its associated data.
    """
    id: int
    """The unique numerical identifier for the VHS collection item."""

    name: str = ""
    """The name of the VHS collection item."""

    description: str = ""
    """The description of the VHS collection item."""