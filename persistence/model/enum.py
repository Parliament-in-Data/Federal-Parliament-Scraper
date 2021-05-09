from enum import Enum

class TimeOfDay(Enum):
    '''
    Meetings of the Parliament can occurr in the Morning, Afternoon or Evening.
    This Enum allows for differentiating between them.
    '''
    AM = 1
    PM = 2
    EVENING = 3

class TopicType(Enum):
    GENERAL = 1  # Topics for which no further subclassification could be made
    CURRENT_AFFAIRS = 2  # Discussion of current news or political affairs
    BUDGET = 3  # Discussions concerning the budget
    SECRET_VOTE = 4  # General secret votes
    REVISION_OF_CONSTITUTION = 5 # Discussion regarding the revision of articles of the constitution
    INTERPELLATION = 6  # Questions submitted by an MP to the Government
    NAME_VOTE = 7  # Public name votes, mostly concerning legislation
    DRAFT_BILL = 8  # Wetsontwerp, a legal initiative coming from the Government
    BILL_PROPOSAL = 9  # Wetsvoorstel, a legal initiative coming from the parliament
    LEGISLATION = 10  # No further distinction could be made if this is a DRAFT or PROPOSAL
    QUESTIONS = 11

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
