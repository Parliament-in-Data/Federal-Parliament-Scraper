from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Member:
    uuid : str
    first_name : str
    last_name :str
    party : str
    province : str
    language : str
    alternative_names : Optional[List[str]]
    replaces : Optional[List[str]]
    activities : Optional[List[str]]
    url : str
    date_of_birth : datetime
    gender : str
    photo_url : Optional[str]
