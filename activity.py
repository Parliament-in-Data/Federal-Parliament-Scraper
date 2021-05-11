# TODO: remove me
'''
from models import Vote
from models.enums import Choice


class Activity:
    """
    An Activity links a member of Parliament to a specific action they performed
    on a given date.
    """

    def __init__(self, member, date):
        self.member = member
        self.date = date

    def dict(self, base_URI):
        raise NotImplementedError()


class VoteActivity(Activity):
    """
    A VoteActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    action is the casting of a name vote.
    """

    def __init__(self, member, vote: Vote, choice: Choice):
        Activity.__init__(self, member, vote.meeting.date)
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
    A TopicActivity represents the fact that the member
    has taken an action in the meeting, in this case the
    this means their name has appeared in a topic in
    the meeting. The section in which this topic appeared
    is recorded as well as the specific meeting.
    """

    def __init__(self, member, meeting, meeting_topic):
        Activity.__init__(self, member, meeting.date)
        self.meeting_topic = meeting_topic

    def dict(self, base_URI):
        return {
            "type": "topic",
            "topic": f'{base_URI}{self.meeting_topic.get_uri()}'
        }


class QuestionActivity(Activity):
    """
    A QuestionActivity represents the fact that the member
    has asked a question (orally or written), a li
    """

    def __init__(self, member, date, question):
        Activity.__init__(self, member, date)
        self.question = question

    def dict(self, base_URI):
        return {
            "type": "question",
            "question": f'{base_URI}{self.question.uri()}'
        }


class LegislativeActivity(Activity):
    """
    A LegislativeActivity represents the fact that the member
    has been the author of a Bill or Bill Proposal.
    """

    def __init__(self, member, date, document):
        Activity.__init__(self, member, date)
        self.document = document

    def dict(self, base_URI):
        return {
            "type": "legislation",
            "document": f'{base_URI}{self.document.uri()}'
        }
'''