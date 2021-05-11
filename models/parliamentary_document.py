from dataclasses import dataclass
from typing import Optional, List
from models import Member
from datetime import datetime


@dataclass
class ParliamentaryDocument:
    document_nr: str
    document_type: str
    title: Optional[str]
    source: str
    date: Optional[datetime]
    descriptor: List[str]
    keywords: List[str]
    authors: List[Member]
