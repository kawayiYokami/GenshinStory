from typing import List, Union, Literal, Optional
from pydantic import BaseModel

class Dialogue(BaseModel):
    type: Literal['dialogue']
    speaker: str
    line: str

class Narrator(BaseModel):
    type: Literal['narrator']
    line: str

class DialogueNode(BaseModel):
    id: str
    option_text: str
    dialogue: List[Union[Dialogue, Narrator]]
    options: List['DialogueNode']  # Recursively reference DialogueNode

# Update forward reference to allow recursive validation
DialogueNode.model_rebuild()

class RogueEvent(BaseModel):
    """Represents a single Simulated Universe event."""
    id: int
    title: str
    location: Optional[str] = None
    possible_outcomes: Optional[List[str]] = None
    dialogue_tree: Optional[DialogueNode] = None
