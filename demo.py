#%%
from parliament_session import ParliamentarySession
from data_store import CompoundDataStore
from models.enums import TopicType
#%%
session = ParliamentarySession(55, CompoundDataStore([]))
# Get an object containing all known members during the session
session.get_members()
# Get all plenary meeting
meetings = session.get_plenary_meetings()
# %%
# For a single meeting a lot of information is available
topics = meetings[0].topics[TopicType.NAME_VOTE]
for idx in reversed(list(topics.keys())):
    print(f"{idx}. {topics[idx].title.NL}")
    if topics[idx].votes:
        vote = topics[idx].votes[0]
        print(vote)
        print("Ja: %s" % ([str(voter) for voter in vote.yes_voters]))
        print("Nee: %s" % ([str(voter) for voter in vote.no_voters]))
        print("Onthouding: %s" % ([str(voter) for voter in vote.abstention_voters]))
