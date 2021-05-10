#from extras_mongoengine.fields import EnumField
from mongoengine.fields import ReferenceField, DateField, StringField

from persistence.model.model import Model
import persistence.model.member
from persistence.model.vote import Vote
from persistence.model.meeting import MeetingTopic
from persistence.model.question import Question
from persistence.model.document import Document
from persistence.model.enum import Choice

class Activity(Model):
    member = ReferenceField(Member, required=True)
    date = DateField(required=True)

    meta = { 'abstract': True }

class VoteActivity(Activity):
    vote = ReferenceField(Vote, required=True)
    #choice = EnumField(Choice)

class TopicActivity(Activity):
    meeting_topic = ReferenceField(MeetingTopic)

class QuestionActivity(Activity):
    question = ReferenceField(Question)

class LegislativeActivity(Activity):
    document = ReferenceField(Document)
