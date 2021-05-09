from mongoengine.fields import ReferenceField, IntField, ListField, DateField

from persistence.model.model import Model
from persistence.model.meeting import Meeting
from persistence.model.member import Member
from persistence.model.question import Question
from persistence.model.document import Document

class Session(Model):
    session_nr = IntField(required=True, min_value=52, max_value=55)
    start = DateField()
    end = DateField()

    plenary_meetings = ListField(ReferenceField(Meeting))
    members = ListField(ReferenceField(Member))
    questions = ListField(ReferenceField(Question))
    documents = ListField(ReferenceField(Document))
