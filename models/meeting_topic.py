from dataclasses import dataclass
from typing import List
from models.enums import TimeOfDay
from datetime import datetime


@dataclass
class NlFrTitle:
    NL: str
    FR: str

@dataclass
class MeetingTopic:
    meeting_id: int
    id: int
    title: NlFrTitle
    votes: List[any] # TODO
    questions: List[any] # TODO
    legislations: List[any] # TODO
