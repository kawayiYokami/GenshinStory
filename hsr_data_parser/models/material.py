from dataclasses import dataclass

@dataclass
class Material:
    """Represents a material or item in the game."""
    id: int
    name: str
    description: str
    background_description: str
    main_type: str
    sub_type: str
    rarity: str