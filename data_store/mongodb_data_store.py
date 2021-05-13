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
        # Save all the topics, so we can access them
        for topic in meeting['topics']:
            topic.save()
        
        # Update the topics list
        meeting['meeting'].topics = list(map(lambda topic_id: MeetingTopic.objects.get(id = topic_id), meeting['topic_ids']))
        meeting['meeting'].save()

    @wrap_document
    def store_legislation(self, legislation):
        legislation.save()

    @wrap_question
    def store_question(self, question):
        question.save()

    def contains_meeting(self, id):
        return Meeting.objects(id = id).count() >= 1

    def contains_meeting_topic(self, id):
        return True

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
