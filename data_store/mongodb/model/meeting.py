#from extras_mongoengine.fields import EnumField
from mongoengine.fields import ReferenceField, DateTimeField, IntField, ListField, StringField, EnumField, EmbeddedDocumentField

from data_store.mongodb.model import Model, CompoundKey, Vote, Document, Question, DocumentID, QuestionID
from models.enums import TopicType, TimeOfDay

class Meeting(Model):
    id = IntField(required=True, primary_key=True)
    session_nr = IntField()
    time_of_day = EnumField(TimeOfDay)
    date = DateTimeField()
    topics = ListField(ReferenceField('MeetingTopic'))

class MeetingTopicID(CompoundKey):
    session_nr = IntField()
    meeting_id = IntField()
    topic_id = IntField()

# TODO: Maybe it's better to not work with lists here
# Alternatives:
# Link to meeting in votes, documents, questions
# OR use embedded documents (maybe with lazy loading)
class MeetingTopic(Model):
    id = EmbeddedDocumentField(MeetingTopicID, primary_key=True)
    session_nr = IntField()
    meeting_id = IntField()
    topic_id = IntField()
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
                topic_id = MeetingTopicID(
                    session_nr = topic.session_nr,
                    meeting_id = topic.meeting.id,
                    topic_id = topic.id
                )
                meeting_topics.append(
                    MeetingTopic(
                        id = topic_id,
                        session_nr = topic.session_nr,
                        meeting_id = topic.meeting.id,
                        topic_id = topic.id,
                        topic_type = topic_type,
                        meeting = topic.meeting.id,
                        titleNL = topic.title.NL,
                        titleFR = topic.title.FR,
                        votes = [], #TODO: list(map(lambda vote: vote.id, topic.votes))
                        legislations = list(map(lambda document: 
                            Document.objects.get(id = DocumentID(session_nr = document.session_nr, document_nr = document.document_nr)), 
                            topic.legislations)),
                        questions = list(map(lambda question: 
                            Question.objects.get(id = QuestionID(session_nr = question.session_nr, document_nr = question.document_nr)), 
                            topic.questions))
                    )
                )
                topic_ids.append(topic_id)

        wrapped_meeting = Meeting(
            id = meeting.id,
            session_nr = meeting.session_nr,
            time_of_day = meeting.time_of_day,
            date = meeting.date
        )
        return func(self, { 'meeting': wrapped_meeting, 'topics': meeting_topics, 'topic_ids': topic_ids })
    return wrapper