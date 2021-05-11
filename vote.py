from util import clean_string
from bs4 import NavigableString
from typing import List
import activity
from models.enums import Choice
from models import MeetingTopic, GenericVote, LanguageGroupVote, ElectronicGenericVote, ElectronicAdvisoryVote


def electronic_vote_from_table(meeting_topic: MeetingTopic, vote_number: int, vote_start_node: NavigableString):
    """Generate a new electronic (advisory or generic) vote from a parsed table.

    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        vote_start_node (NavigableString): Vote start node as obtained by BeautifulSoup

    Returns:
        Vote: 
    """

    yes = int(clean_string(vote_start_node.find_all(
        'td')[1].find('p').get_text()))
    vote_end_node = vote_start_node.find_next_sibling().find_next_sibling()
    if not vote_end_node or vote_end_node.name != 'table':
        return ElectronicAdvisoryVote(meeting_topic, vote_number, yes, False)

    no = int(clean_string(vote_end_node.find_all(
        'td')[1].find('p').get_text()))

    return ElectronicGenericVote(meeting_topic, vote_number, yes, False, no)


def generic_vote_from_table(meeting_topic: MeetingTopic, vote_number: int, vote_rows: NavigableString):
    """Generate a new GenericVote from a parsed table.

    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

    Returns:
        GenericVote (optional):
    """
    yes_str = clean_string(vote_rows[1].find_all(
        'td')[1].find('p').get_text())
    if not yes_str:
        # Sometimes, tables are empty... example: https://www.dekamer.be/doc/PCRI/html/55/ip100x.html
        return None
    yes = int(yes_str)
    no = int(clean_string(vote_rows[2].find_all(
        'td')[1].find('p').get_text()))
    abstention = int(clean_string(
        vote_rows[3].find_all('td')[1].find('p').get_text()))

    return GenericVote(meeting_topic, vote_number, yes, False, no, abstention)

def language_group_vote_from_table(meeting_topic: MeetingTopic, vote_number: int, vote_rows: NavigableString):
    """Generate a new Vote from a parsed table.

    Args:
        meeting_topic (MeetingTopic): The meeting topic
        vote_number (int): Number of the vote in this meeting (e.g. 1)
        vote_rows (NavigableString): Vote rows as obtained by BeautifulSoup

    Returns:
        LanguageGroupVote: 
    """
    yes_fr = int(clean_string(
        vote_rows[2].find_all('td')[1].find('p').get_text()))
    no_fr = int(clean_string(
        vote_rows[3].find_all('td')[1].find('p').get_text()))
    abstention_fr = int(clean_string(
        vote_rows[4].find_all('td')[1].find('p').get_text()))

    yes_nl = int(clean_string(
        vote_rows[2].find_all('td')[3].find('p').get_text()))
    no_nl = int(clean_string(
        vote_rows[3].find_all('td')[3].find('p').get_text()))
    abstention_nl = int(clean_string(
        vote_rows[4].find_all('td')[3].find('p').get_text()))

    return LanguageGroupVote(meeting_topic, vote_number, GenericVote(meeting_topic, vote_number, yes_nl, no_nl, abstention_nl), GenericVote(meeting_topic, vote_number, yes_fr, no_fr, abstention_fr))
