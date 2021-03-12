from meeting import MeetingTopic, Meeting
from member import Member
from vote import Vote
from common import Choice

class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    in a given meeting.
    """
    def __init__(self, member: Member, meeting: Meeting):
        self.member = member
        self.meeting = meeting
    def dict(self, base_URI):
        raise NotImplementedError()


class VoteActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    action is the casting of a name vote.
    """
    def __init__(self, member: Member, meeting: Meeting, vote: Vote, choice: Choice):
        Activity.__init__(self, member, meeting)
        self.vote = vote
        self.choice = choice
    def dict(self, base_URI):
        return {
            "type": "vote",
            "vote": self.vote.vote_number,
            "meeting": f'{base_URI}{self.meeting.url()}',
            "choice": str(self.choice)
        }

class TopicActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    this means their name has appeared in a topic in
    the meeting. The section in which this topic appeared
    is recorded as well as the specific meeting.
    """
    def __init__(self, member, meeting:Meeting, meeting_topic:MeetingTopic):
        Activity.__init__(self, member, meeting)
        self.meeting_topic = meeting_topic
    def dict(self, base_URI):
        # TODO: perhaps we should split off meeting topics into separate json
        return {
            "type": "topic",
            "section": self.meeting_topic.section_NL,
            "item": self.meeting_topic.item,
            "meeting": f'{base_URI}{self.meeting.url()}'
        }
    