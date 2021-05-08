from enum import Enum
from common import Language
from bs4 import BeautifulSoup, NavigableString
import dateparser
import requests
from util import clean_string, go_to_p, clean_list, normalize_str
from vote import GenericVote, LanguageGroupVote, electronic_vote_from_table
import re
from os import path, makedirs
import json
from collections import defaultdict
import parliament_parser
import datetime
from activity import TopicActivity
from document import ParliamentaryDocument, ParliamentaryQuestion
import concurrent.futures
import functools


class TimeOfDay(Enum):
    '''
    Meetings of the Parliament can occurr in the Morning, Afternoon or Evening.
    This Enum allows for differentiating between them.
    '''
    AM = 1
    PM = 2
    EVENING = 3


class TopicType(Enum):
    GENERAL = 1  # Topics for which no further subclassification could be made
    CURRENT_AFFAIRS = 2  # Discussion of current news or political affairs
    BUDGET = 3  # Discussions concerning the budget
    SECRET_VOTE = 4  # General secret votes
    # Discussion regarding the revision of articles of the constitution
    REVISION_OF_CONSTITUTION = 5
    INTERPELLATION = 6  # Questions submitted by an MP to the Government
    NAME_VOTE = 7  # Public name votes, mostly concerning legislation
    DRAFT_BILL = 8  # Wetsontwerp, a legal initiative coming from the Government
    BILL_PROPOSAL = 9  # Wetsvoorstel, a legal initiative coming from the parliament
    LEGISLATION = 10  # No further distinction could be made if this is a DRAFT or PROPOSAL
    QUESTIONS = 11

    @staticmethod
    def from_section_and_title(title_NL: str, section_NL: str):
        title_NL = title_NL.lower()
        section_NL = section_NL.lower()
        if 'begroting' in section_NL:
            return TopicType.BUDGET
        if 'actualiteitsdebat' in section_NL:
            return TopicType.CURRENT_AFFAIRS
        if 'naamstemming' in section_NL:
            return TopicType.NAME_VOTE
        if 'geheim' in section_NL and 'stemming' in section_NL:
            return TopicType.SECRET_VOTE
        if 'vragen' in section_NL or 'vragen' in title_NL or 'vraag' in title_NL:
            return TopicType.QUESTIONS
        if 'interpellatie' in section_NL:
            return TopicType.INTERPELLATION
        if 'herziening' in section_NL and 'grondwet' in section_NL:
            return TopicType.REVISION_OF_CONSTITUTION
        if 'ontwerp' in section_NL or 'voorstel' in section_NL:
            if (not 'ontwerp' in section_NL) or 'voorstel' in title_NL:
                return TopicType.BILL_PROPOSAL
            if (not 'voorstel' in section_NL) or 'ontwerp' in title_NL:
                return TopicType.DRAFT_BILL
            return TopicType.GENERAL
        return TopicType.GENERAL


class Meeting:
    """
    A Meeting represents the meeting notes for a gathering of the federal parliament.
    """
    language_mapping = {
        Language.NL: ('Titre1NL', 'Titre2NL'),
        Language.FR: ('Titre1FR', 'Titre2FR'),
    }

    def __init__(self, session, id: int, time_of_day: TimeOfDay, date: datetime.datetime):
        """
        Initiate a new Meeting instance

        Args:
            session (parliament_parser.ParliamentarySession): The related session of the parliament
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

    def get_uri(self):
        return f'meetings/{self.id}.json'

    def dump_json(self, base_path: str, base_URI="/"):
        base_meeting_path = path.join(base_path, "meetings")
        base_meeting_URI = f'{base_URI}meetings/'
        resource_name = f'{self.id}.json'

        makedirs(base_meeting_path, exist_ok=True)

        if not self.topics:
            self.get_meeting_topics()

        topics = defaultdict(dict)
        for key in self.topics:
            topic = self.topics[key]
            topics[str(topic.topic_type)][topic.item] = topic

        with open(path.join(base_meeting_path, resource_name), 'w+') as fp:
            json.dump({
                'id': self.id,
                'time_of_day': str(self.time_of_day),
                'date': self.date.isoformat(),
                'topics': {
                    topic_type: {
                        topic_item: topic_value.dump_json(base_path, base_URI)
                        for topic_item, topic_value in topic_type_dict.items()
                    }
                    for topic_type, topic_type_dict in topics.items()
                },
            }, fp, ensure_ascii=False)

        meeting_dir_path = path.join(base_meeting_path, str(self.id))
        makedirs(meeting_dir_path, exist_ok=True)

        with open(path.join(meeting_dir_path, 'unfolded.json'), 'w+') as fp:
            json.dump({
                topic_type: {
                    topic_item: topic_value.json_representation(base_URI)
                    for topic_item, topic_value in topic_type_dict.items()
                }
                for topic_type, topic_type_dict in topics.items()
            }, fp, ensure_ascii=False)

        return f'{base_meeting_URI}{resource_name}'

    def __repr__(self):
        return 'Meeting(%s, %s, %s, %s)' % (self.session, self.id, self.time_of_day, repr(self.date))

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
        This internal method adds information on the votes to MeetingTopics
        '''
        soup = self.__get_soup()

        print('currently checking:', self.get_notes_url())

        def extract_title_by_vote(table: NavigableString, language: Language):
            class_name = Meeting.language_mapping[language][1]

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
                    vote = GenericVote.from_table(
                        self.topics[agenda_item], vote_number, rows)
                elif len(rows) == 6:
                    vote = LanguageGroupVote.from_table(
                        self.topics[agenda_item], vote_number, rows)
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
            dict(MeetingTopic): The topics discussed in this meeting
        """
        if refresh or not self.topics:
            # Obtain the meeting notes
            soup = self.__get_soup()
            self.topics = {}

            def parse_topics(language):
                classes = Meeting.language_mapping[language]
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
                        self.topics[item] = MeetingTopic(
                            self.parliamentary_session, self, item)
                    self.topics[item].set_title(
                        language, current_title.rstrip())
                    self.topics[item].set_section(language, clean_string(section.text) if section else (
                        "Algemeen" if language == Language.NL else "Generale"))
                    self.topics[item].complete_type()
                    if language == Language.NL:
                        title = normalize_str(current_title.rstrip().lower()).decode()
                        for member in self.parliamentary_session.get_members():
                            if member.normalized_name() in title:
                                member.post_activity(TopicActivity(
                                    member, self, self.topics[item]))
                    current_title = ""

            # Parse Dutch Meeting Topics
            parse_topics(Language.NL)

            # Parse French Meeting Topics
            parse_topics(Language.FR)
            self.__get_votes()
        return self.topics

    @staticmethod
    def from_soup(meeting: NavigableString, session):
        """Generate a new Meeting instance from BeautifulSoup's objects

        Args:
            meeting (NavigableString): The table row representing the meeting
            session (parliament_parser.ParliamentarySession): The parliamentary session this meeting is a part of.

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

        result = Meeting(session, meeting_id, tod, date)
        return result


def create_or_get_doc(session, number):
    return ParliamentaryDocument(session, number) if number not in session.documents else session.documents[number]


def create_or_get_question(session, number):
    return ParliamentaryQuestion(session, number) if number not in session.questions else session.questions[number]


class MeetingTopic:
    """
    A MeetingTopic represents a single agenda point
    in a meeting of the parliament.
    """

    def __init__(self, session, meeting: Meeting, item: int):
        """Constructs a new instance of a MeetingTopic

        Args:
            session (ParliamentarySession): Session of the parliament
            id (int): Number of the meeting this topic is part of (e.g. 89)
            item (int): The number of the agenda item (e.g. 1)
        """
        self.parliamentary_session = session
        self.session = session.session
        self.meeting = meeting
        self.id = meeting.id
        self.item = item
        self.topic_type = TopicType.GENERAL
        self.votes = []
        self.related_documents = []
        self.related_questions = []

    def get_uri(self):
        return f'meetings/{self.id}/{self.item}.json'

    def json_representation(self, session_base_URI: str):
        return {'id': self.item, 'title': {'NL': self.title_NL, 'FR': self.title_FR}, 'votes': [
                      vote.to_dict(session_base_URI) for vote in self.votes], 'questions': [f'{session_base_URI}{question.uri()}' for question in self.related_questions], 'legislation': [f'{session_base_URI}{document.uri()}' for document in self.related_documents]}

    def dump_json(self, base_path: str, session_base_URI: str):
        topic_path = path.join(base_path, 'meetings', str(self.id))
        makedirs(topic_path, exist_ok=True)

        with open(path.join(topic_path, f'{self.item}.json'), 'w+') as fp:
            json.dump(self.json_representation(session_base_URI), fp, ensure_ascii=False)

        return f'{session_base_URI}{self.get_uri()}'

    def __repr__(self):
        return "MeetingTopic(%s, %s, %s)" % (self.session, self.id, self.item)

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
        # Don't multithread this too much, since that causes more load to the site
        # which means we get blocked, and it also increases the lock contention.
        if self.topic_type == TopicType.BILL_PROPOSAL or self.topic_type == TopicType.DRAFT_BILL or self.topic_type == TopicType.LEGISLATION or self.topic_type == TopicType.NAME_VOTE or self.topic_type == TopicType.SECRET_VOTE:
            bill_numbers = []
            for line in self.title_NL.split('\n'):
                match = re.match(".*\(([0-9]+)\/.*\)", line)
                if match and match.group(1):
                    bill_numbers.append(match.group(1))
            self.related_documents = list(map(functools.partial(
                create_or_get_doc, self.parliamentary_session), bill_numbers))
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
            self.related_questions = list(map(functools.partial(
                create_or_get_question, self.parliamentary_session), questions_numbers))

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
