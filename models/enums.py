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

    @staticmethod
    def from_section_and_title(title_NL: str, section_NL: str):
        title_NL = title_NL.lower()
        section_NL = section_NL.lower()
        if 'begroting' in section_NL:
            return TopicType.BUDGET
        if 'actualiteitsdebat' in section_NL:
            return TopicType.CURRENT_AFFAIRS
        if 'naamstemming' in section_NL:
            return TopicType.NAME_VOTE
        if 'geheim' in section_NL and 'stemming' in section_NL:
            return TopicType.SECRET_VOTE
        if 'vragen' in section_NL or 'vragen' in title_NL or 'vraag' in title_NL:
            return TopicType.QUESTIONS
        if 'interpellatie' in section_NL:
            return TopicType.INTERPELLATION
        if 'herziening' in section_NL and 'grondwet' in section_NL:
            return TopicType.REVISION_OF_CONSTITUTION
        if 'ontwerp' in section_NL or 'voorstel' in section_NL:
            if (not 'ontwerp' in section_NL) or 'voorstel' in title_NL:
                return TopicType.BILL_PROPOSAL
            if (not 'voorstel' in section_NL) or 'ontwerp' in title_NL:
                return TopicType.DRAFT_BILL
            return TopicType.GENERAL
        return TopicType.GENERAL

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
