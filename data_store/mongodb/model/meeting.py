#from extras_mongoengine.fields import EnumField
from mongoengine.fields import ReferenceField, DateTimeField, IntField, ListField, StringField, EnumField

from data_store.mongodb.model import Model, Vote, Document, Question
from models.enums import TopicType, TimeOfDay

class Meeting(Model):
    id = IntField(required=True, primary_key=True)
    session_nr = IntField()
    time_of_day = EnumField(TimeOfDay)
    date = DateTimeField()
    topics = ListField(ReferenceField('MeetingTopic'))

# TODO: Maybe it's better to not work with lists here
# Alternatives:
# Link to meeting in votes, documents, questions
# OR use embedded documents (maybe with lazy loading)
class MeetingTopic(Model):
    id = StringField(required=True, primary_key=True)
    session_nr = IntField()
    topic_type = EnumField(TopicType)
    meeting = ReferenceField(Meeting)
    titleNL = StringField()
    titleFR = StringField()
    votes = ListField(ReferenceField(Vote))
    legislations = ListField(ReferenceField(Document))
    questions = ListField(ReferenceField(Question))

def wrap_meeting(func):
    def wrapper(self, meeting):
        meeting_topics = []
        topic_ids = []
        for topic_type, topic_dict in meeting.topics.items():
            for i, topic in topic_dict.items():
                meeting_topics.append(
                    MeetingTopic(
                        id = str(topic.session_nr) + ' ' + str(topic.meeting.id) + ' ' + str(topic.id),
                        session_nr = topic.session_nr,
                        topic_type = topic_type,
                        meeting = topic.meeting.id,
                        titleNL = topic.title.NL,
                        titleFR = topic.title.FR,
                        votes = [], #TODO: list(map(lambda vote: vote.id, topic.votes))
                        legislations = list(map(lambda document: 
                            str(document.session_nr) + ' ' + document.document_nr, topic.legislations)),
                        questions = list(map(lambda question: 
                            str(question.session_nr) + ' ' + question.document_nr, topic.questions))
                    )
                )
                topic_ids.append(topic.id)

        wrapped_meeting = Meeting(
            id = meeting.id,
            session_nr = meeting.session_nr,
            time_of_day = meeting.time_of_day,
            date = meeting.date,
            topics = topic_ids
        )
        return func(self, { 'meeting': wrapped_meeting, 'topics': meeting_topics })
    return wrapper
