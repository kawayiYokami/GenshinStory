from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from ._core import BaseWikiModel

class QuestMetadata(BaseModel):
    task_name: Optional[str] = Field(None, alias='任务名')
    task_area: Optional[str] = Field(None, alias='任务地区')
    task_type: Optional[str] = Field(None, alias='任务类型')
    open_level: Optional[str] = Field(None, alias='开放等级')
    task_description: Optional[str] = Field(None, alias='任务描述')
    reward: Optional[str] = Field(None, alias='奖励')

class DialogueLine(BaseModel):
    type: Literal['dialogue']
    speaker: str
    line: str

class DescriptionLine(BaseModel):
    type: Literal['description']
    text: str

class QuoteLine(BaseModel):
    type: Literal['quote']
    text: str

class NarratorLine(BaseModel):
    type: Literal['narrator']
    line: str

class OptionsGroup(BaseModel):
    type: Literal['options_group']
    choices: List[OptionChoice]

AnyDialoguePart = Union[DialogueLine, DescriptionLine, QuoteLine, NarratorLine, OptionsGroup]

class OptionChoice(BaseModel):
    option: str
    reply: Optional[List[AnyDialoguePart]] = None

class Quest(BaseWikiModel):
    id: int
    name: str = Field(..., alias='title')
    metadata: Optional[QuestMetadata] = None
    process: Optional[List[str]] = None
    dialogue: Optional[List[AnyDialoguePart]] = None

# Update forward references to allow for recursive models
OptionsGroup.model_rebuild()
OptionChoice.model_rebuild()
