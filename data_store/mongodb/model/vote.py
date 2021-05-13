from mongoengine import StringField, ReferenceField, IntField, BooleanField, ListField, EnumField

from data_store.mongodb.model import Model

import models as m

class Vote(Model):
    meeting_topic = ReferenceField('MeetingTopic')
    vote_type = EnumField(m.VoteType)
    vote_nr = IntField()
    yes = IntField()
    no = IntField()
    abstention = IntField()
    yes_voters = ListField(ReferenceField('Member'))
    no_voters = ListField(ReferenceField('Member'))
    abstention_voters = ListField(ReferenceField('Member'))
    vote_NL = ReferenceField('Vote')
    vote_FR = ReferenceField('Vote')
    unsure = BooleanField()

#def vote_wrapper(self, vote):
#    if isinstance(vote, m.GenericVote):
#        return Vote(
#            meeting_topic = vote.meeting_topic,
#            vote_type = m.VoteType.GENERIC_VOTE,
#            vote_number = vote.vote_number,
#            yes = vote.yes,
#            no = vote.no,
#            abstention = vote.abstention,
#            yes_voters = list(map(lambda member: member.uuid, vote.yes_voters)),
#            no_voters = list(map(lambda member: member.uuid, vote.no_voters)),
#            abstention_voters = list(map(lambda member: member.uuid, vote.abstention_voters)),
#            unsure = vote.unsure
#        )
#
#    elif isinstance(vote, m.LanguageGroupVote):
#        return Vote(
#            meeting_topic = vote.meeting_topic,
#            vote_type = m.VoteType.LANGUAGE_GROUP_VOTE,
#            vote_number = vote.vote_number,
#            yes = vote.yes,
#            no = vote.no,
#            abstention = vote.abstention,
#            yes_voters = list(map(lambda member: member.uuid, vote.yes_voters)),
#            no_voters = list(map(lambda member: member.uuid, vote.no_voters)),
#            abstention_voters = list(map(lambda member: member.uuid, vote.abstention_voters)),
#            vote_nl = vote.vote_NL,
#            vote_fr = [],
#            unsure = vote.unsure
#        )
#
#    elif isinstance(vote, m.ElectronicGenericVote):
#        pass
#
#    elif isinstance(vote, ElectronicAdvisoryVote):
#        pass
#
## class GenericVote(Vote):
##     no = IntField()
##     abstention = IntField()
##     yes_voters = ListField(ReferenceField(Member))
##     no_voters = ListField(ReferenceField(Member))
##     abstention_voters = ListField(ReferenceField(Member))
## 
## class LanguageGroupVote(Vote):
##     no = IntField()
##     abstention = IntField()
##     yes_voters = ListField(ReferenceField(Member))
##     no_voters = ListField(ReferenceField(Member))
##     abstention_voters = ListField(ReferenceField(Member))
##     vote_NL = ReferenceField('Vote')
##     vote_FR = ReferenceField('Vote')
## 
## class ElectronicGenericVote(Vote):
##     no = IntField()
## 
## class ElectronicAdvisoryVote(Vote):
##     pass
##