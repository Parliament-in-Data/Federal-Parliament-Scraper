from mongoengine import connect, disconnect

from data_store import DataStore
from data_store.mongodb.model import *

class MongoDBDataStore(DataStore):
    '''
    The MongoDB data store
    '''

    def __init__(self, db_name):
        super().__init__()
        connect(host=db_name)

    def finish(self):
        disconnect()

    @wrap_member
    def store_member(self, member):
        #member.save()
        pass

    @wrap_meeting
    def store_meeting(self, meeting):
        for topic in meeting['topics']:
            topic.save()
        meeting['meeting'].save()

    @wrap_document
    def store_legislation(self, legislation):
        if not self.contains_document({ 'session_nr': legislation.session_nr, 'document_nr': legislation.document_nr }):
            legislation.save()

    @wrap_question
    def store_question(self, question):
        if not self.contains_question({ 'session_nr': question.session_nr, 'document_nr': question.document_nr }):
            question.save()

    def contains_meeting(self, id):
        return Meeting.objects(id = id).count() >= 1

    def contains_meeting_topic(self, id):
        pass

    def contains_document(self, id):
        return Document.objects(
            session_nr = id['session_nr'],
            document_nr = id['document_nr']
        ).count() >= 1

    def contains_question(self, id):
        return Question.objects(
            session_nr = id['session_nr'],
            document_nr = id['document_nr']
        ).count() >= 1
