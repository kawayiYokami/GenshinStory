from dataclasses import dataclass

@dataclass
class Book:
    """Represents a single in-game book or readable item."""
    id: int
    name: str
    content: str
    series_id: int