from dataclasses import dataclass
from typing import Optional, List
from models import Member
from datetime import datetime


@dataclass
class ParliamentaryQuestion:
    document_nr: str
    title: Optional[str]
    source: str
    date: Optional[datetime]
    responding_minister: Optional[str]
    responding_department: Optional[str]
    authors: List[Member]
