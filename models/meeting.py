from dataclasses import dataclass
from typing import Dict
from models.enums import TimeOfDay, TopicType
from models import MeetingTopic
from datetime import datetime


@dataclass
class Meeting:
    id: int
    time_of_day: TimeOfDay
    date: datetime
    topics: Dict[TopicType, Dict[int, MeetingTopic]]
