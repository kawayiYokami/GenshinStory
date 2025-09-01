from dataclasses import dataclass


@dataclass
class Weapon:
    """
    Represents a game weapon with its associated data.
    """
    id: int
    """The unique numerical identifier for the weapon."""

    name: str = ""
    """The name of the weapon."""

    description: str = ""
    """The functional description of the weapon."""

    story: str = ""
    """The background story or lore of the weapon."""

    model_id: str = ""
    """The internal model identifier for the weapon (e.g., Weapon_B_Common_01)."""