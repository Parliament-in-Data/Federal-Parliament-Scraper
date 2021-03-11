from enum import Enum
from common import Language
from bs4 import BeautifulSoup
import dateparser
import requests
from util import clean_string, go_to_p, clean_list
from vote import Vote, LanguageGroupVote
import re
from os import path, makedirs
import json
from collections import defaultdict

class TimeOfDay(Enum):
    '''
    Meetings of the Parliament can occurr in the Morning, Afternoon or Evening.
    This Enum allows for differentiating between them.
    '''
    AM = 1
    PM = 2
    EVENING = 3


class MeetingTopic:
    """
    A MeetingTopic represents a single agenda point
    in a meeting of the parliament.
    """

    def __init__(self, session, id, item):
        """Constructs a new instance of a MeetingTopic

        Args:
            session (int): Session number of the parliament (e.g. 55)
            id (int): Number of the meeting this topic is part of (e.g. 89)
            item (int): The number of the agenda item (e.g. 1)
        """
        self.session = session
        self.id = id
        self.item = item
        self.votes = []

    def to_dict(self, session_base_URI):
        return {'id': self.item, 'title': {'NL': self.title_NL, 'FR': self.title_FR}, 'votes': [vote.to_dict(session_base_URI) for vote in self.votes]}

    def __repr__(self):
        return "MeetingTopic(%s, %s, %s)" % (self.session, self.id, self.item)

    def set_title(self, language, title):
        """Set the title of this agenda item for a specific language

        Args:
            language (Language): The language of this title (e.g. Language.NL)
            title (str): The actual title
        """
        if language == Language.NL:
            self.title_NL = title
        else:
            self.title_FR = title
    
    def set_section(self, language, section_name):
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

class Meeting:
    """
    A Meeting represents the meeting notes for a gathering of the federal parliament.
    """
    language_mapping = {
        Language.NL : ('Titre1NL', 'Titre2NL'),
        Language.FR : ('Titre1FR', 'Titre2FR'),
    }
    def __init__(self, session, id, time_of_day, date):
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
    def dump_json(self, base_path, base_URI="/"):
        base_meeting_path = path.join(base_path, "meetings")
        base_meeting_URI = f'{base_URI}meetings/'
        resource_name = f'{self.id}.json'

        makedirs(base_meeting_path, exist_ok=True)

        if not self.topics:
            self.get_meeting_topics()

        topics = defaultdict(list)
        for key in self.topics:
            topic = self.topics[key]
            topics[topic.get_section()[0]].append(topic.to_dict(base_URI))


        with open(path.join(base_meeting_path, resource_name), 'w+') as fp:
            json.dump({
                'id': self.id,
                'time_of_day': str(self.time_of_day),
                'date': self.date.isoformat(),
                'topics': topics
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
    def __get_votes(self):
        '''
        This internal method adds information on the votes to MeetingTopics
        '''
        page = requests.get(self.get_notes_url())
        soup = BeautifulSoup(page.content, 'html.parser')

        print('currently checking:', self.get_notes_url())

        def extract_title_by_vote(table, language):
            class_name = Meeting.language_mapping[language][1]

            next_line = table.find_previous_sibling("p", {"class": class_name})
            while not re.match(r"([0-9]+) (.)*", clean_string(next_line.text)):
                next_line = next_line.find_previous_sibling("p", {"class": class_name})
            
            match = re.match(r"([0-9]+) (.*)", clean_string(next_line.text))
            return int(match.group(1))


        def get_name_votes():
            votes_nominatifs = []
            s3 = soup.find('div', {'class': 'Section3'})
            if s3:
                tags = s3.find_all(text=re.compile('Vote\s*nominatif\s*-\s*Naamstemming:'))
                for i, tag in enumerate(tags):
                        vote_header = go_to_p(tag)
                        yes = []
                        no = []
                        abstention = []

                        current_node = vote_header
                        
                        while not current_node.name == "table":
                            current_node = current_node.find_next_sibling()
                        current_node = current_node.find_next_sibling()
                        yes = clean_string(current_node.get_text())
                        while not current_node.name == "table":
                            if current_node.get_text():
                                yes += clean_string(current_node.get_text())
                            current_node = current_node.find_next_sibling()

                        yes = clean_list(yes.split(','))

                        current_node = current_node.find_next_sibling()
                        no = clean_string(current_node.get_text())
                        while not current_node.name == "table":
                            if current_node.get_text():
                                no += clean_string(current_node.get_text())
                            current_node = current_node.find_next_sibling()

                        no = clean_list(no.split(','))

                        next_vote = go_to_p(tags[i+1]).find_previous_sibling() if i + 1 < len(tags) else vote_header.parent.find_all('p')[-1]
                        current_node = next_vote
                        abstention = clean_string(current_node.get_text())
                        while not current_node.name == "table":
                            if current_node.get_text():
                                abstention = clean_string(current_node.get_text()) + abstention
                            current_node = current_node.find_previous_sibling()
                        abstention = clean_list(abstention.split(','))

                        votes_nominatifs.append(( yes, no, abstention))
            return votes_nominatifs
        name_votes = get_name_votes()
        for tag in soup.find_all(text=re.compile('Stemming/vote ([0-9]+)')):
                vote_number = int(re.match('\(?Stemming/vote ([0-9]+)\)?', tag).group(1))
                table = tag.findParent('table')
                if table:
                    agenda_item = extract_title_by_vote(table, Language.FR)
                    agenda_item1 = extract_title_by_vote(table, Language.NL)
                    assert(agenda_item1 == agenda_item)

                    # Some pages have a height="0" override tag to fix browser display issues.
                    # We have to ignore these otherwise we would start interpreting the votes as the wrong type.
                    rows = table.find_all('tr', attrs={'height': None})

                    if len(rows) == 5:
                        vote = Vote.from_table(vote_number, rows)
                    elif len(rows) == 6:
                        vote = LanguageGroupVote.from_table(vote_number, rows)
                    else:
                        continue

                    if vote_number - 1 < len(name_votes):
                        names = name_votes[vote_number - 1]
                        vote.set_yes_voters([self.parliamentary_session.find_member(name) for name in names[0]])
                        vote.set_no_voters([self.parliamentary_session.find_member(name) for name in names[1]])
                        vote.set_abstention_voters([self.parliamentary_session.find_member(name) for name in names[2]])

                    self.topics[agenda_item].add_vote(vote)
    def get_meeting_topics(self, refresh = False):
        """Obtain the topics for this meeting.

        Args:
            refresh (bool, optional): Force a refresh of the meeting notes. Defaults to False.

        Returns:
            dict(MeetingTopic): The topics discussed in this meeting
        """
        if refresh or not self.topics:
            # Obtain the meeting notes
            page = requests.get(self.get_notes_url())
            soup = BeautifulSoup(page.content, 'html.parser')
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
                        current_title = clean_string(item.text) + '\n' + current_title
                        item = titles.pop()
                    m = re.match("([0-9]+) (.*)", clean_string(item.text))

                    current_title = m.group(2) + '\n' + current_title
                    section = item.find_previous_sibling("p", {"class": classes[0]})

                    item = int(m.group(1))
                    if not item in self.topics:
                        self.topics[item] = MeetingTopic(self.session, self.id, item)
                    self.topics[item].set_title(language, current_title.rstrip())
                    self.topics[item].set_section(language, clean_string(section.text) if section else ("Algemeen" if language == Language.NL else "Generale" ))
                    current_title = ""

            # Parse Dutch Meeting Topics
            parse_topics(Language.NL)
            
            # Parse French Meeting Topics
            parse_topics(Language.FR)
            self.__get_votes()
        return self.topics
    def from_soup(meeting, session):
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

        result = Meeting(session, meeting_id, tod, date)
        return result
