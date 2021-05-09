from mongoengine.fields import ReferenceField, IntField, StringField, ListField, DateField

from persistence.model.model import Model
from persistence.model.session import Session
from persistence.model.member import Member

class Document(Model):
    session = ReferenceField(Session)
    document_number = IntField()
    descriptor = StringField()
    keywords = ListField(StringField())
    title = StringField()
    document_type = StringField()
    date = DateField()
    authors = ListField(ReferenceField(Member))
