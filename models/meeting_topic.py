from dataclasses import dataclass
from typing import List
from models.enums import TimeOfDay
from models import ParliamentaryDocument, ParliamentaryQuestion
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
    votes: List['Vote']
    legislations: List[ParliamentaryDocument]
    questions: List[ParliamentaryQuestion]
