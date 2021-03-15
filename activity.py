from vote import Vote
from common import Choice

class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    in a given meeting.
    """
    def __init__(self, member, meeting):
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
    def __init__(self, member, vote: Vote, choice: Choice):
        Activity.__init__(self, member, vote.meeting)
        self.vote = vote
        self.choice = choice
    def dict(self, base_URI):
        return {
            "type": "vote",
            "topic": f'{base_URI}{self.vote.meeting_topic.get_uri()}',
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
    def __init__(self, member, meeting, meeting_topic):
        Activity.__init__(self, member, meeting)
        self.meeting_topic = meeting_topic
    def dict(self, base_URI):
        return {
            "type": "topic",
            "topic": f'{base_URI}{self.meeting_topic.get_uri()}'
        }
    