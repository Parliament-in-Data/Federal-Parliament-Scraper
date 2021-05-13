from mongoengine.fields import ReferenceField, IntField, StringField, ListField, DateTimeField

from data_store.mongodb.model import Model
from data_store.mongodb.model import Member

class Document(Model):
    id = StringField(primary_key=True)
    session_nr = IntField()
    document_nr = StringField()
    document_type = StringField()
    title = StringField()
    source = StringField()
    date = DateTimeField()
    descriptor = ListField(StringField())
    keywords = ListField(StringField())
    authors = ListField(ReferenceField(Member))

def wrap_document(func):
    def wrapper(self, document):
        wrapped_document = Document(
            id = str(document.session_nr) + ' ' + document.document_nr,
            session_nr = document.session_nr,
            document_nr = document.document_nr,
            document_type = document.document_type,
            title = document.title,
            source = document.source,
            date = document.date,
            descriptor = document.descriptor,
            keywords = document.keywords,
            authors = list(map(lambda member: member.uuid, document.authors))
        )
        return func(self, wrapped_document)
    return wrapper