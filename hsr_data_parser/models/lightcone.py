from dataclasses import dataclass

@dataclass
class LightCone:
    """Represents a Light Cone equipment item."""
    id: int
    name: str
    description: str
    background_description: str
    rarity: str