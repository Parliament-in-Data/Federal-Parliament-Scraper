from dataclasses import dataclass
from typing import List, Optional
from models.enums import TimeOfDay
from datetime import datetime


@dataclass:
class NlFrTitle:
    NL: str
    FR: str

@dataclass
class MeetingTopic:
    id: int
    title: NlFrTitle
    votes: List[any] # TODO
    questions: List[any] # TODO
    legislations: List[any] # TODO
