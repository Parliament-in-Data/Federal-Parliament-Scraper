from mongoengine import connect, disconnect

from data_store import DataStore
from data_store.mongodb.model import wrap_member
from data_store.mongodb.model import wrap_question
from data_store.mongodb.model import wrap_document

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

    def store_meeting(self, meeting):
        pass

    @wrap_document
    def store_legislation(self, legislation):
        legislation.save()

    @wrap_question
    def store_question(self, question):
        question.save()
