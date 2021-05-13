from mongoengine import ReferenceField, IntField, ListField, StringField, DateTimeField

from data_store.mongodb.model import Model, Member

class Question(Model):
    session_nr = IntField()
    document_nr = StringField()
    title = StringField()
    source = StringField()
    date = DateTimeField()
    responding_minister = StringField()
    responding_department = StringField()
    authors = ListField(ReferenceField(Member))

    meta = {
        'indexes': [
            {
                'fields': ['session_nr', 'document_nr'], 
                'unique': True
            }
        ]
    }

def wrap_question(func):
    def wrapper(self, question):
        wrapped_question = Question(
            session_nr = question.session_nr,
            document_nr = question.document_nr,
            title = question.title,
            source = question.source,
            date = question.date,
            responding_minister = question.responding_minister,
            responding_department = question.responding_department,
            authors = list(map(lambda member: member.uuid, question.authors))
        )
        return func(self, wrapped_question)
    return wrapper