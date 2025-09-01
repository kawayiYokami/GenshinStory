from dataclasses import dataclass, field
from typing import List

@dataclass
class Partner:
    """
    Represents a game partner/character with all associated data.
    """
    id: str
    """The unique identifier for the partner."""

    name: str = ""
    """The name of the partner."""

    outlook_desc: str = ""
    """The partner's appearance description."""

    profile_descs: List[str] = field(default_factory=list)
    """A list of the partner's profile descriptions.
    Multiple entries are possible (e.g., hidden descriptions).
    """

    impression_f: str = ""
    """Impression text for female player characters (玲的印象)."""

    impression_m: str = ""
    """Impression text for male player characters (哲的印象)."""

    true_name: str = ""
    """The partner's true or international name."""

    birthday: str = ""
    """The partner's birthday, stored as a localized string."""