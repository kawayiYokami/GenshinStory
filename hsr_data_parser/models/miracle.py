from dataclasses import dataclass

@dataclass
class Miracle:
    """Represents a Rogue-like miracle (Curio) in the game."""
    id: int
    name: str
    background_description: str