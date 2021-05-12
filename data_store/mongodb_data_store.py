from mongoengine import connect, disconnect

from data_store import DataStore
from data_store.mongodb.model import wrap_member
from data_store.mongodb.model import wrap_question
from data_store.mongodb.model import wrap_document
from data_store.mongodb.model import wrap_meeting

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
        member.save()

    @wrap_meeting
    def store_meeting(self, meeting):
        for topic in meeting['topics']:
            topic.save()
        meeting['meeting'].save()

    @wrap_document
    def store_legislation(self, legislation):
        legislation.save()

    @wrap_question
    def store_question(self, question):
        question.save()
