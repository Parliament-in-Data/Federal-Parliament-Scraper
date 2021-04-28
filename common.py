from enum import Enum


class Language(Enum):
    '''
    Enum used to differentiate between the two languages used in the meetings
    of the parliament.
    '''
    NL = 0
    FR = 1


class Choice(Enum):
    '''
    Enum used to differentiate between the two languages used in the meetings
    of the parliament.
    '''
    NO = 0
    YES = 1
    ABSTENTION = 2
