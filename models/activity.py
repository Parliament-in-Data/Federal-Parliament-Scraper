from dataclasses import dataclass
from models import Vote, Member, MeetingTopic
from datetime import datetime
from models.enums import Choice
from models import ParliamentaryQuestion, ParliamentaryDocument


@dataclass
class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    on a given date.
    """
    member: Member
    date: datetime

@dataclass
class VoteActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    action is the casting of a name vote.
    """
    vote: Vote
    choice: Choice

@dataclass
class TopicActivity(Activity):
    """
    A TopicActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    this means their name has appeared in a topic in
    the meeting. The section in which this topic appeared
    is recorded as well as the specific meeting.
    """
    meeting_topic: MeetingTopic

@dataclass
class QuestionActivity(Activity):
    """
    A QuestionActivity represents the fact that the member
    has asked a question (orally or written), a li
    """
    question: ParliamentaryQuestion

@dataclass
class LegislativeActivity(Activity):
    """
    A LegislativeActivity represents the fact that the member
    has been the author of a Bill or Bill Proposal.
    """
    document: ParliamentaryDocument
