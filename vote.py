from util import clean_string
from bs4 import NavigableString
from typing import List
import activity
from common import Choice

def post_vote_activity(vote, choice, members):
    for member in members:
        member.post_activity(activity.VoteActivity(member, vote, choice))

class Vote:
    """A Vote represents a single vote in a meeting.
    """

    def __init__(self, meeting_topic, vote_number: int, yes: int, no: int, abstention: int):
        """A Vote represents a single vote in a meeting.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            yes (int): Number of yes votes
            no (int): Number of no votes
            abstention (int): Number of abstentions
        """
        self.meeting = meeting_topic.meeting
        self.meeting_topic = meeting_topic
        self.vote_number = vote_number
        self.yes = yes
        self.yes_voters = []
        self.no = no
        self.no_voters = []
        self.abstention = abstention
        self.abstention_voters = []
        self.unsure = False

    def __repr__(self):
        return "Vote(%d, %d, %d, %d)" % (self.vote_number, self.yes, self.no, self.abstention)

    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number,
            'type': 'general',
            'yes': self.yes,
            'no': self.no,
            'abstention': self.abstention,
            'passed': self.has_passed(),
            'voters': {
                "yes": [f'{session_base_URI}members/{member.uuid}.json' for member in self.yes_voters],
                "no": [f'{session_base_URI}members/{member.uuid}.json' for member in self.no_voters],
                "abstention": [f'{session_base_URI}members/{member.uuid}.json' for member in self.abstention_voters]
            }
        }

    def has_passed(self):
        """Does this motion have the majority of votes

        Returns:
            bool: Does this motion have the majority of votes
        """
        # FIXME: No Quorum Check (rule 42.5 of parliament)
        return self.yes > self.no + self.abstention
    @staticmethod
    def from_table(meeting_topic, vote_number:int, vote_rows:NavigableString):
        """Generate a new Vote from a parsed table.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

        Returns:
            Vote: 
        """
        yes = int(clean_string(vote_rows[1].find_all('td')[1].find('p').get_text()))
        no = int(clean_string(vote_rows[2].find_all('td')[1].find('p').get_text()))
        abstention = int(clean_string(vote_rows[3].find_all('td')[1].find('p').get_text()))

        return Vote(meeting_topic, vote_number, yes, no, abstention)

    def set_yes_voters(self, l):
        """Set the members who voted for

        Args:
            l (List[Member]): A list of Members who voted for
        """
        if abs(len(l) - self.yes) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(f'NOTE: The number of yes voters did not match the provided list: {len(l)} instead of {self.yes}')
            self.unsure = True
        self.yes = len(l)
        self.yes_voters = l
        post_vote_activity(self, Choice.YES, l)

    def set_no_voters(self, l):
        """Set the members who voted against

        Args:
            l (List[Member]): A list of Members who voted against
        """
        if abs(len(l) - self.no) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(f'NOTE: The number of no voters did not match the provided list: {len(l)} instead of {self.no}')
            self.unsure = True
        self.no = len(l)
        self.no_voters = l
        post_vote_activity(self, Choice.NO, l)


    def set_abstention_voters(self, l):
        """Set the members who abstained from voting for this motion

        Args:
            l (List[Member]): A list of Members who abstained from the vote
        """
        if abs(len(l) - self.abstention) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(f'NOTE: The number of abstention voters did not match the provided list: {len(l)} instead of {self.abstention}')
            self.unsure = True
        self.abstention = len(l)
        self.abstention_voters = l
        post_vote_activity(self, Choice.ABSTENTION, l)



class LanguageGroupVote(Vote):
    """For some voting matters a majority in both Language Groups is needed"""

    def __init__(self, meeting_topic, vote_number: int, vote_NL: Vote, vote_FR: Vote):
        """For some voting matters a majority in both Language Groups is needed

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_NL (Vote): The Vote in the Dutch-speaking part of the Parliament
            vote_FR (Vote): The Vote in the French-speaking part of the Parliament
        """
        Vote.__init__(self, meeting_topic, vote_number, vote_NL.yes + vote_FR.yes, vote_NL.no + vote_FR.no, vote_NL.abstention + vote_FR.abstention)
        self.vote_NL = vote_NL
        self.vote_FR = vote_FR

    def __repr__(self):
        return "LanguageGroupVote(%d, %d, %d)" % (self.vote_number, self.vote_NL, self.vote_FR)

    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number,
            'type': 'language_group',
            'yes': self.vote_NL.yes + self.vote_FR.yes,
            'no': self.vote_NL.no + self.vote_FR.no,
            'abstention': self.vote_NL.abstention + self.vote_FR.abstention,
            'passed': self.has_passed(),
            'voters': {
                "yes": [f'{session_base_URI}members/{member.uuid}' for member in self.yes_voters],
                "no": [f'{session_base_URI}members/{member.uuid}' for member in self.no_voters],
                "abstention": [f'{session_base_URI}members/{member.uuid}' for member in self.abstention_voters]
            },
            'detail': {
                "NL": self.vote_NL.to_dict(session_base_URI),
                "FR": self.vote_FR.to_dict(session_base_URI)
            }
        }

    def has_passed(self):
        """The vote has to pass in both halves of the parliament.

        Returns:
            bool: Has the vote obtained the necessary majority?
        """
        return self.vote_NL.has_passed() and self.vote_FR.has_passed()

    @staticmethod
    def from_table(meeting_topic, vote_number: int, vote_rows: NavigableString):
        """Generate a new Vote from a parsed table.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

        Returns:
            Vote: 
        """
        yes_fr = int(clean_string(vote_rows[2].find_all('td')[1].find('p').get_text()))
        no_fr = int(clean_string(vote_rows[3].find_all('td')[1].find('p').get_text()))
        abstention_fr = int(clean_string(vote_rows[4].find_all('td')[1].find('p').get_text()))

        yes_nl = int(clean_string(vote_rows[2].find_all('td')[3].find('p').get_text()))
        no_nl = int(clean_string(vote_rows[3].find_all('td')[3].find('p').get_text()))
        abstention_nl = int(clean_string(vote_rows[4].find_all('td')[3].find('p').get_text()))

        return LanguageGroupVote(meeting_topic, vote_number, Vote(meeting_topic, vote_number, yes_nl, no_nl, abstention_nl), Vote(meeting_topic, vote_number, yes_fr, no_fr, abstention_fr))


class ElectronicVote(Vote):
    """Some voting are anonymously organised electronically. We don't have the names in this case"""

    def __init__(self, meeting_topic, vote_number: int, yes: int, no: int):
        """A Vote represents a single vote in a meeting.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            yes (int): Number of yes votes
            no (int): Number of no votes
        """
        Vote.__init__(self, meeting_topic, vote_number, yes, no, 0)

    def __repr__(self):
        return f"ElectronicVote({self.vote_number}, {self.yes}, {self.no})"

    def to_dict(self, session_base_URI: str):
        return {
            'id': self.vote_number,
            'type': 'electronic',
            'yes': self.yes,
            'no': self.no,
            'passed': self.has_passed()
        }

    @staticmethod
    def from_table(meeting_topic, vote_number: int, vote_start_node: NavigableString):
        """Generate a new Vote from a parsed table.

        Args:
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_start_node (NavigableString): Vote start node as obtained by BeautifulSoup

        Returns:
            Optional[Vote]: 
        """

        yes = int(clean_string(vote_start_node.find_all('td')[1].find('p').get_text()))
        vote_end_node = vote_start_node.find_next_sibling().find_next_sibling()
        if not vote_end_node or vote_end_node.name != 'table':
            return None

        no = int(clean_string(vote_end_node.find_all('td')[1].find('p').get_text()))

        return ElectronicVote(meeting_topic, vote_number, yes, no)
