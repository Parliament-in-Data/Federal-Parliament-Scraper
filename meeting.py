from enum import Enum
from models.enums import Language
from bs4 import BeautifulSoup, NavigableString
import dateparser
import requests
from util import clean_string, go_to_p, clean_list
from vote import electronic_vote_from_table, generic_vote_from_table, language_group_vote_from_table
import re
from os import path, makedirs
import json
from collections import defaultdict
import datetime
#from activity import TopicActivity
from models.enums import TimeOfDay, TopicType
from models import Meeting, MeetingTopic, NlFrTitle
import concurrent.futures
import functools


class MeetingBuilder:
    """
    A MeetingBuilder builds the meeting notes for a gathering of the federal parliament.
    """
    language_mapping = {
        Language.NL: ('Titre1NL', 'Titre2NL'),
        Language.FR: ('Titre1FR', 'Titre2FR'),
    }

    def __init__(self, session, id: int, time_of_day: TimeOfDay, date: datetime.datetime):
        """
        Initiate a new Meeting instance

        Args:
            session (ParliamentarySession): The related session of the parliament
            id (int): The number of the meeting (e.g. 1)
            time_of_day (TimeOfDay): The time of day this meeting occured at
            date (date): The date on which the meeting took place
        """
        self.parliamentary_session = session
        self.session = self.parliamentary_session.session
        self.id = id
        self.time_of_day = time_of_day
        self.date = date
        self.topics = {}
        self._cached_soup = None

    def to_data(self):
        topics = defaultdict(dict)
        for topic in self.topics.values():
            topics[topic.topic_type][topic.id] = topic
        return Meeting(
            self.id,
            self.time_of_day,
            self.date,
            {
                topic_type: {
                    id: topic.to_data()
                    for id, topic in topics.items()
                }
                for topic_type, topics in topics.items()
            }
        )

    def get_notes_url(self):
        """Obtain the URL of the meeting notes.

        Returns:
            str: URL of the related meeting notes.
        """
        return 'https://www.dekamer.be/doc/PCRI/html/%d/ip%03dx.html' % (self.session, self.id)

    def __get_soup(self):
        if not self._cached_soup:
            page = self.parliamentary_session.requests_session.get(self.get_notes_url())
            self._cached_soup = BeautifulSoup(page.content, 'lxml', from_encoding='windows-1252')
        return self._cached_soup

    def __get_votes(self):
        '''
        This internal method adds information on the votes to MeetingTopicBuilders
        '''
        soup = self.__get_soup()

        print('currently checking:', self.get_notes_url())

        def extract_title_by_vote(table: NavigableString, language: Language):
            class_name = MeetingBuilder.language_mapping[language][1]

            next_line = table.find_previous_sibling("p", {"class": class_name})
            while not re.match(r"([0-9]+) (.)*", clean_string(next_line.text)):
                next_line = next_line.find_previous_sibling(
                    "p", {"class": class_name})

            match = re.match(r"([0-9]+) (.*)", clean_string(next_line.text))
            return int(match.group(1))

        def extract_vote_number_from_tag(tag, default):
            header = clean_string(tag.find_parent('p').get_text())
            numeric_values = [int(s) for s in header.split() if s.isdigit()]
            return numeric_values[0] if numeric_values else default

        def extract_name_list_from_under_table(current_node):
            name_list = clean_string(current_node.get_text())
            while not (current_node.name == "table" or 'naamstemming' in current_node.get_text().lower()):
                if current_node.get_text():
                    name_list += ',' + clean_string(current_node.get_text())
                current_node = current_node.find_next_sibling()

            name_list = clean_list(name_list.split(','))
            return name_list, current_node

        def is_vote_cancelled(current_node):
            cancelled = False

            while current_node and not current_node.name == "table":
                # Sometimes votes get cancelled, apparently
                # this check seems to be consistent
                if 'annulé' in current_node.get_text().lower() or '42.5' in current_node.get_text().lower():
                    cancelled = True
                    break
                current_node = current_node.find_next_sibling()

            return cancelled, current_node

        def get_name_and_electronic_votes():
            name_votes = {}
            electronic_votes = {}
            s3 = soup.find('div', {'class': 'Section3'})
            if s3:
                tags = s3.find_all(text=re.compile(
                    r'Vote\s*nominatif\s*-\s*Naamstemming:'))
                tags += s3.find_all(text=re.compile(
                    r'Naamstemming\s*-\s*Vote\s*nominatif:'))
                for i, tag in enumerate(tags):
                    vote_number = extract_vote_number_from_tag(tag, i)
                    vote_header = go_to_p(tag)
                    cancelled, current_node = is_vote_cancelled(vote_header)
                    if cancelled:
                        continue

                    yes, current_node = extract_name_list_from_under_table(
                        current_node.find_next_sibling())
                    no, current_node = extract_name_list_from_under_table(
                        current_node.find_next_sibling())

                    abstention = []

                    # Handles the case where the abstention box is missing (no abstentions)
                    if 'onthoudingen' in current_node.get_text().lower() or 'abstentions' in current_node.get_text().lower():
                        next_vote = go_to_p(tags[i+1]).find_previous_sibling() if i + 1 < len(
                            tags) else vote_header.parent.find_all('p')[-1]
                        current_node = next_vote
                        abstention = clean_string(current_node.get_text())
                        current_node = current_node.find_previous_sibling()

                        # TODO: merge with function
                        while not (current_node.name == "table" or 'naamstemming' in current_node.get_text().lower()):
                            if current_node.get_text():
                                abstention = clean_string(
                                    current_node.get_text()) + ',' + abstention
                            current_node = current_node.find_previous_sibling()
                        abstention = clean_list(abstention.split(','))

                    name_votes[vote_number] = (yes, no, abstention)

                tags = s3.find_all(text=re.compile(
                    r'Comptage\s*électronique\s*–\s*Elektronische telling:'))
                for i, tag in enumerate(tags):
                    vote_number = extract_vote_number_from_tag(tag, i)
                    vote_header = go_to_p(tag)
                    cancelled, current_node = is_vote_cancelled(vote_header)

                    if cancelled:
                        continue

                    electronic_votes[vote_number] = current_node

            return name_votes, electronic_votes

        name_votes, electronic_votes = get_name_and_electronic_votes()

        for tag in soup.find_all(text=re.compile(r'(Stemming/vote|Vote/stemming)\s+([0-9]+)')):
            vote_number = int(
                re.match(r'\(?(Stemming/vote|Vote/stemming)\s+([0-9]+)\)?', tag).group(2))
            is_electronic_vote = vote_number in electronic_votes

            # Structure for electronic votes is a little different. This case is not inside a table.
            if is_electronic_vote:
                while tag.name != 'p':
                    tag = tag.parent
            else:
                for _ in range(0, 6):
                    if tag:
                        tag = tag.parent

                # Fixes an issue where votes are incorrectly parsed because of the fact a quorum was not reached
                # (in that case no table is present but the table encapsulating the report can be)
                if not tag or tag.name != 'table':
                    continue

            agenda_item = extract_title_by_vote(tag, Language.FR)
            agenda_item1 = extract_title_by_vote(tag, Language.NL)
            assert agenda_item1 == agenda_item

            if not is_electronic_vote and len(tag.find_all('tr', attrs={'height': None})) <= 6:
                # Some pages have a height="0" override tag to fix browser display issues.
                # We have to ignore these otherwise we would start interpreting the votes as the wrong type.
                rows = tag.find_all('tr', attrs={'height': None})
                vote = None

                # We can't always rely on the number of rows, since sometimes there's randomly an empty row.
                if len(rows) == 5 or (len(rows) == 6 and rows[-1].get_text().strip() == ''):
                    vote = generic_vote_from_table(self.topics[agenda_item], vote_number, rows)
                elif len(rows) == 6:
                    vote = language_group_vote_from_table(self.topics[agenda_item], vote_number, rows)
                if not vote:
                    continue
                if vote_number in name_votes:
                    names = name_votes[vote_number]
                    vote.set_yes_voters(
                        [self.parliamentary_session.find_member(name) for name in names[0]])
                    vote.set_no_voters(
                        [self.parliamentary_session.find_member(name) for name in names[1]])
                    vote.set_abstention_voters(
                        [self.parliamentary_session.find_member(name) for name in names[2]])

                self.topics[agenda_item].add_vote(vote)
            elif is_electronic_vote:
                vote = electronic_vote_from_table(
                    self.topics[agenda_item], vote_number, electronic_votes[vote_number])
                self.topics[agenda_item].add_vote(vote)

    def get_meeting_topics(self, refresh=False):
        """Obtain the topics for this meeting.

            refresh (bool, optional): Force a refresh of the meeting notes. Defaults to False.

        Returns:
            dict(MeetingTopicBuilder): The topics discussed in this meeting
        """
        if refresh or not self.topics:
            # Obtain the meeting notes
            soup = self.__get_soup()
            self.topics = {}

            def parse_topics(language):
                classes = MeetingBuilder.language_mapping[language]
                titles = soup.find_all('p', {'class': classes[1]})
                current_title = ""

                while titles:
                    item = titles.pop()
                    if not clean_string(item.text):
                        continue
                    while not re.match("([0-9]+) (.*)", clean_string(item.text)):
                        current_title = clean_string(
                            item.text) + '\n' + current_title
                        item = titles.pop()
                    m = re.match("([0-9]+) (.*)", clean_string(item.text))

                    current_title = m.group(2) + '\n' + current_title
                    section = item.find_previous_sibling(
                        "p", {"class": classes[0]})

                    item = int(m.group(1))
                    if not item in self.topics:
                        self.topics[item] = MeetingTopicBuilder(
                            self.parliamentary_session, self, item)
                    self.topics[item].set_title(
                        language, current_title.rstrip())
                    self.topics[item].set_section(language, clean_string(section.text) if section else (
                        "Algemeen" if language == Language.NL else "Generale"))
                    self.topics[item].complete_type()
                    current_title = ""

            # Parse Dutch Meeting Topics
            parse_topics(Language.NL)

            # Parse French Meeting Topics
            parse_topics(Language.FR)
            self.__get_votes()
        return self.topics

def meeting_from_soup(meeting: NavigableString, session):
    """Generate a new Meeting instance from BeautifulSoup's objects

    Args:
        meeting (NavigableString): The table row representing the meeting
        session (ParliamentarySession): The parliamentary session this meeting is a part of.

    Returns:
        Meeting: A Meeting object representing this meeting.
    """
    meeting = meeting.find_all('td')
    meeting_id = int(meeting[0].text.strip())
    date = dateparser.parse(meeting[2].text.strip())
    tod = TimeOfDay.AM
    if 'PM' in meeting[1].text:
        tod = TimeOfDay.PM
    elif 'Avond' in meeting[1].text:
        tod = TimeOfDay.EVENING

    result = MeetingBuilder(session, meeting_id, tod, date)
    result.get_meeting_topics()
    return result.to_data()

class MeetingTopicBuilder:
    """
    A MeetingTopicBuilder builds a single agenda point
    in a meeting of the parliament.
    """

    def __init__(self, session, meeting: MeetingBuilder, id: int):
        """Constructs a new instance of a MeetingTopicBuilder

        Args:
            session (ParliamentarySession): Session of the parliament
            id (int): Number of the meeting this topic is part of (e.g. 89)
            id (int): The number of the agenda item (e.g. 1)
        """
        self.parliamentary_session = session
        self.session = session.session
        self.meeting = meeting
        self.id = id
        self.topic_type = TopicType.GENERAL
        self.votes = []
        self.related_documents = []
        self.related_questions = []

    def to_data(self):
        return MeetingTopic(self.meeting, self.id, NlFrTitle(self.title_NL, self.title_FR), self.votes, self.related_documents, self.related_questions)

    def set_title(self, language: Language, title: str):
        """Set the title of this agenda item for a specific language

        Args:
            language (Language): The language of this title (e.g. Language.NL)
            title (str): The actual title
        """
        if language == Language.NL:
            self.title_NL = title
        else:
            self.title_FR = title

    def complete_type(self, type: TopicType = None):
        if type:
            self.topic_type = type
        else:
            self.topic_type = TopicType.from_section_and_title(
                self.title_NL, self.section_NL)
        # No multithreading here, since that causes more load to the site
        # which means we get blocked, and it also increases the lock contention.
        if self.topic_type == TopicType.BILL_PROPOSAL or self.topic_type == TopicType.DRAFT_BILL or self.topic_type == TopicType.LEGISLATION or self.topic_type == TopicType.NAME_VOTE or self.topic_type == TopicType.SECRET_VOTE:
            bill_numbers = []
            for line in self.title_NL.split('\n'):
                match = re.match(".*\(([0-9]+)\/.*\)", line)
                if match and match.group(1):
                    bill_numbers.append(match.group(1))
            self.related_documents = [x for x in map(
                self.parliamentary_session.create_or_get_document, bill_numbers) if x]
        elif self.topic_type == TopicType.QUESTIONS:
            questions_numbers = []
            for line in self.title_NL.split('\n'):
                new_format_match = re.match(".*\(([0-9]{8}(P|C))\)", line)
                if new_format_match and new_format_match.group(1):
                    questions_numbers.append(new_format_match.group(1))
                else:
                    old_format_match = re.match(
                        ".*\(nr\.? (P[0-9]{4})\)", line)
                    if old_format_match and old_format_match.group(1):
                        questions_numbers.append(
                            f'{self.session}{old_format_match.group(1)}')
            self.related_questions = [x for x in map(
                self.parliamentary_session.create_or_get_question, questions_numbers) if x]

    def set_section(self, language: Language, section_name: str):
        """The meeting is also organized in sections, this method allows you to set
        the section name.

        Args:
            language (Language): The language of this section name (e.g. Language.NL)
            section_name (str): The actual section name
        """
        if language == Language.NL:
            self.section_NL = section_name
        else:
            self.section_FR = section_name

    def get_title(self):
        """Returns the title of the agenda item

        Returns:
            (str, str): A pair of strings where the first element is
                        the Dutch version of the title, the second is
                        the French version.
        """
        return (self.title_NL, self.title_FR)

    def get_section(self):
        """Returns the section name of the agenda item

        Returns:
            (str, str): A pair of strings where the first element is
                        the Dutch version of the title, the second is
                        the French version.
        """
        return (self.section_NL, self.section_FR)

    def add_vote(self, vote):
        """Add votes to the agenda item

        Args:
            vote (Vote): Add a single vote to the agenda item 
        """
        self.votes.append(vote)

    def get_votes(self):
        """Get the votes for the agenda item.

        Returns:
            list(Vote): A list of all the votes related to the item.
        """
        return self.votes
