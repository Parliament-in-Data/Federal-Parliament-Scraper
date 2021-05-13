from mongoengine import ReferenceField, IntField, ListField, StringField, DateTimeField, EmbeddedDocumentField

from data_store.mongodb.model import Model, CompoundKey, Member

class QuestionID(CompoundKey):
    session_nr = IntField()
    document_nr = StringField()

class Question(Model):
    id = EmbeddedDocumentField(QuestionID, primary_key=True)
    session_nr = IntField()
    document_nr = StringField()
    title = StringField()
    source = StringField()
    date = DateTimeField()
    responding_minister = StringField()
    responding_department = StringField()
    authors = ListField(ReferenceField(Member))

def wrap_question(func):
    def wrapper(self, question):
        wrapped_question = Question(
            id = QuestionID(
                session_nr = question.session_nr,
                document_nr = question.document_nr
            ),
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