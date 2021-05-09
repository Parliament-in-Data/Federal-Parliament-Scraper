from extras_mongoengine.fields import EnumField
from mongoengine.fields import ReferenceField, DateField, IntField, ListField

from persistence.model.model import Model
from persistence.model.session import Session
from persistence.model.document import Document
from persistence.model.question import Question
from persistence.model.vote import Vote
from persistence.model.enum import TimeOfDay, TopicType

class Meeting(Model):
    session = ReferenceField(Session)
    meeting_nr = IntField()
    time_of_day = EnumField(TimeOfDay)
    date = DateField()
    topics = ListField(ReferenceField(MeetingTopic))

class MeetingTopic(Model):
    session = ReferenceField(Session)
    meeting = ReferenceField(Meeting)
    meeting_topic_nr = IntField()
    topic_type = EnumField(TopicType)
    votes = ListField(ReferenceField(Vote))
    related_documents = ListField(ReferenceField(Document))
    related_questions = ListField(ReferenceField(Question))
