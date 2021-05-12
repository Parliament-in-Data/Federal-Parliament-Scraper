from mongoengine import ReferenceField, IntField, ListField, StringField, DateTimeField

from data_store.mongodb.model import Model
from data_store.mongodb.model import Member

class Question(Model):
    document_nr = IntField()
    title = StringField()
    source = StringField()
    date = DateTimeField()
    responding_minister = StringField()
    responding_department = StringField()
    # TODO: has to be ReferenceField(Member), but for early stages, use the string
    # Mainly to prevent changing too much code at once
    authors = ListField(StringField())

def wrap_question(func):
    def wrapper(self, question):
        wrapped_question = Member(
            document_nr = question.document_nr,
            title = question.title,
            source = question.source,
            date = question.date,
            responding_minister = question.responding_minister,
            responding_department = question.responding_department,
            authors = question.authors
        )
        return func(self, wrapped_question)
    return wrapper