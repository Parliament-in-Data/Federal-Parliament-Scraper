from mongoengine.fields import ReferenceField, IntField, BooleanField, ListField

from persistence.model.model import Model
from persistence.model.meeting import Meeting, MeetingTopic
from persistence.model.member import Member

class Vote(Model):
    meeting = ReferenceField(Meeting, required=True)
    meeting_topic = ReferenceField(MeetingTopic, required=True)
    vote_number = IntField(required=True)
    yes = IntField(required=True)
    unsure = BooleanField(default=False)

    meta = { 'abstract': True }

class GenericVote(Vote):
    yes_voters = ListField(ReferenceField(Member))
    no = IntField()
    no_voters = ListField(ReferenceField(Member))
    abstention = IntField()
    abstention_voters = ListField(ReferenceField(Member))

class LanguageGroupVote(GenericVote):
    vote_nl = ReferenceField(Vote)
    vote_fr = ReferenceField(Vote)

class ElectronicGenericVote(Vote):
    no = IntField()

class ElectronicAdvisoryVote(Vote):
    pass
