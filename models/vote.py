from dataclasses import dataclass, field
from typing import List
from models import MeetingTopic, Member


@dataclass
class Vote:
    """A Vote represents a single vote in a meeting."""
    meeting_topic: MeetingTopic
    vote_number: int
    yes: int
    unsure: bool

@dataclass
class GenericVote(Vote):
    """A Vote represents a single vote in a meeting."""
    no: int
    abstention: int
    yes_voters: List[Member] = field(default_factory=list)
    no_voters: List[Member] = field(default_factory=list)
    abstention_voters: List[Member] = field(default_factory=list)

    def has_passed(self):
        """Does this motion have the majority of votes

        Returns:
            bool: Does this motion have the majority of votes
        """
        # FIXME: No Quorum Check (rule 42.5 of parliament)
        return self.yes > self.no + self.abstention

    def set_yes_voters(self, l: List[Member]):
        """Set the members who voted for

        Args:
            l (List[Member]): A list of Members who voted for
        """
        if abs(len(l) - self.yes) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(
                f'NOTE: The number of yes voters did not match the provided list: {len(l)} instead of {self.yes}')
            self.unsure = True
        self.yes = len(l)
        self.yes_voters = l
        # TODO
        #post_vote_activity(self, Choice.YES, l)

    def set_no_voters(self, l: List[Member]):
        """Set the members who voted against

        Args:
            l (List[Member]): A list of Members who voted against
        """
        if abs(len(l) - self.no) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(
                f'NOTE: The number of no voters did not match the provided list: {len(l)} instead of {self.no}')
            self.unsure = True
        self.no = len(l)
        self.no_voters = l
        # TODO
        #post_vote_activity(self, Choice.NO, l)

    def set_abstention_voters(self, l: List[Member]):
        """Set the members who abstained from voting for this motion

        Args:
            l (List[Member]): A list of Members who abstained from the vote
        """
        if abs(len(l) - self.abstention) > 2:
            # Sometimes there are some inconsistencies in the counts and the reported names
            # We allow some tolerance for this
            print(
                f'NOTE: The number of abstention voters did not match the provided list: {len(l)} instead of {self.abstention}')
            self.unsure = True
        self.abstention = len(l)
        self.abstention_voters = l
        # TODO
        #post_vote_activity(self, Choice.ABSTENTION, l)

class LanguageGroupVote(GenericVote):
    def __init__(self, meeting_topic: MeetingTopic, vote_number: int, vote_NL: Vote, vote_FR: Vote):
        """For some voting matters a majority in both Language Groups is needed

        Args:
            meeting_topic (MeetingTopic): The meeting topic
            vote_number (int): Number of the vote in this meeting (e.g. 1)
            vote_NL (Vote): The Vote in the Dutch-speaking part of the Parliament
            vote_FR (Vote): The Vote in the French-speaking part of the Parliament
        """
        super().__init__(self, meeting_topic, vote_number, vote_NL.yes + vote_FR.yes,
                             False, vote_NL.no + vote_FR.no, vote_NL.abstention + vote_FR.abstention)
        self.vote_NL = vote_NL
        self.vote_FR = vote_FR

    def has_passed(self):
        """The vote has to pass in both halves of the parliament.

        Returns:
            bool: Has the vote obtained the necessary majority?
        """
        return self.vote_NL.has_passed() and self.vote_FR.has_passed()

@dataclass
class ElectronicGenericVote(Vote):
    no: int

    def has_passed(self):
        return self.yes > self.no and self.yes + self.no > 75

@dataclass
class ElectronicAdvisoryVote(Vote):
    def has_passed(self):
        """Does this advisory request reach more than the threshold of 1/3 of the yes votes to pass

        Returns:
            bool: Does this motion have the majority of votes
        """
        return self.yes > 50
