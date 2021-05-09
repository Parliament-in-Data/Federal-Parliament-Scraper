from mongoengine import ReferenceField, IntField, ListField, StringField, DateField

from persistence.model.model import Model
from persistence.model.session import Session
from persistence.model.member import Member

class Question(Model):
    session = ReferenceField(Session)
    document_nr = IntField()
    authors = ListField(ReferenceField(Member))
    title = StringField()
    responding_minister = ReferenceField(Member)
    date = DateField()
