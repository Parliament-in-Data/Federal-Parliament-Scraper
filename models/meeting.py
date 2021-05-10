from dataclasses import dataclass
from typing import List, Optional
from models.enums import TimeOfDay
from datetime import datetime

@dataclass
class Meeting:
    id: int
    time_of_day: TimeOfDay
    date: datetime
    topics: List[any] # TODO
