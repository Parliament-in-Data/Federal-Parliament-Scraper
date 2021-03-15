#%%
from parliament_parser import ParliamentarySession
session = ParliamentarySession(54)
# Get an object containing all known members during the session
session.get_members()
# Get all plenary meeting
meetings = session.get_plenary_meetings()
# %%
# For a single meeting a lot of information is available
topics = meetings[0].get_meeting_topics() # <- This is a dict mapping the agenda item number onto an object
for idx in reversed(list(topics.keys())):
    print("%d. %s" % (idx, topics[idx].get_title()[0])) # <- Textual objects (titles and section names) are stored as tuples 
    if topics[idx].get_votes():                         #    containing NL on position 0 and FR on position 1.
        vote = topics[idx].get_votes()[0]
        print(vote)
        print("Ja: %s" % ([str(voter) for voter in vote.yes_voters]))
        print("Nee: %s" % ([str(voter) for voter in vote.no_voters]))
        print("Onthouding: %s" % ([str(voter) for voter in vote.abstention_voters]))

#%%
for meeting in meetings:
    meeting.get_meeting_topics()
# %%
result
# %%
[act for act in session.find_member("Calvo Kristof").activities]
# %%
i = 0
for member in session.get_members():
    if member.activities:
        i+=1
        print(member)
# %%
i