import json
import requests
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from models import Member
from meeting import meeting_from_soup
from document import parliamentary_document_from_nr, parliamentary_question_from_nr
import json
from os import path
import functools
from util import normalize_str
import concurrent.futures
from data_store import DataStore


class ParliamentarySession:
    '''
    A ParliamentarySession object is the main entryway to the scraper.
    It is constructed based on the Session one wants to obtain information on.
    From there information can be obtained on the members of the parliament in that session and its meetings.
    '''
    sessions = {
        55: {'from': '2019-06-20', 'to': '2024-06-19'},
        54: {'from': '2014-06-19', 'to': '2019-04-25'},
        53: {'from': '2010-06-13', 'to': '2014-04-24'},
        52: {'from': '2007-06-10', 'to': '2010-05-06'},
    }

    def __init__(self, session: int, data_store: DataStore):
        """Initialize a new instance of the scraper

        Args:
            session (int): Specify the session for which the scraper should be constructed
        Note:
            Only sessions 55 to 52 are supported for now.
        """
        self.session = session
        self.plenary_meetings = []
        self.members_dict = {}
        self.questions = {}
        self.documents = {}
        self.members = []
        self._members_fn_ln = {}
        self._members_ln_fn = {}
        self._requests_session = requests.Session()
        retry_strategy = Retry(total=5, backoff_factor=1)
        self._requests_session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retry_strategy))
        self.data_store = data_store

    @property
    def requests_session(self):
        return self._requests_session

    def create_or_get_document(self, number):
        if number not in self.documents:
            document = parliamentary_document_from_nr(self, number)
            if not document:
                return None
            self.data_store.store_legislation(document)
            self.documents[number] = document
        return self.documents[number]

    def create_or_get_question(self, number):
        if number not in self.questions:
            question = parliamentary_question_from_nr(self, number)
            if not question:
                return None
            self.data_store.store_question(question)
            self.questions[number] = question
        return self.questions[number]

    def store(self):
        self.get_members()

        for member in self.members:
            self.data_store.store_member(member)

        self.get_plenary_meetings()

        for meeting in self.plenary_meetings:
            self.data_store.store_meeting(meeting)

        self.data_store.finish()

    def find_member(self, query: str):
        """Using their name as listed in the meeting notes
        find the Member object related.

        Args:
            query (str): String formatted as is typical in the meeting notes ("{last_name} {first_name}")

        Returns:
            Member: returns the related Member if one is found.
        """
        if not self.members:
            self.get_members()
        normalized = normalize_str(query)

        if normalized in self._members_fn_ln:
            return self._members_fn_ln[normalized]

        for member in self.members:
            if member.has_name(query):
                return member
        print(f'Undefined member: {query}')

    def get_members_dict(self):
        if not self.members_dict:
            self.members_dict = {}
            for member in self.members:
                first_name = normalize_str(member.first_name).decode()
                last_name = normalize_str(member.last_name).decode()
                self.members_dict[f'{first_name}, {last_name}'] = member
                self.members_dict[f'{first_name}, {last_name} {member.party}'] = member
                self.members_dict[f'{first_name}, {last_name}, {member.party}'] = member
                self.members_dict[f'{first_name}, {last_name}'.replace('-', ' ')] = member
                if member.party == "Vooruit":
                    self.members_dict[f'{first_name}, {last_name}, sp.a'] = member
                    self.members_dict[f'{first_name}, {last_name} sp.a'] = member
        return self.members_dict

    def get_plenary_meetings(self, refresh=False):
        """This API returns an overview of all Plenary meetings in the session.
        A list of Meeting objects is returned.

        Args:
            refresh (bool, optional): Should we fully reparse the scraped document? Defaults to False.

        Returns:
            list(Meeting): List of all known plenary meetings.
        """

        if refresh or not self.plenary_meetings:
            URL = 'https://www.dekamer.be/kvvcr/showpage.cfm?section=/cricra&language=nl&cfm=dcricra.cfm?type=plen&cricra=cri&count=all&legislat=%02d' % (
                self.session)
            page = self.requests_session.get(URL)
            soup = BeautifulSoup(page.content, 'lxml')
            meetings = soup.find_all('tr')

            # Limiting the workers helps with reducing the lock contention.
            # With more workers there is little to gain.
            meetings = meetings[:5] # TODO
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                self.plenary_meetings = list(executor.map(functools.partial(lambda meeting: meeting_from_soup(meeting, self)), meetings))

        return self.plenary_meetings

    def get_members(self):
        """Get all known parliament members within this session

        Returns:
            list(Member): list of all known members within the session
        """
        if not self.members:
            uuid_set = set()

            with open(f'data/composition/{self.session}.json') as json_file:
                data = json.load(json_file)
                for entry in data:
                    member = Member.from_json(entry)
                    assert not member.uuid in uuid_set, "UUID of member is not unique!"
                    self.members.append(member)
                    uuid_set.add(member.uuid)
                # Now that we have all members, link them
                for member, entry in zip(self.members, data):
                    if 'replaces' in entry:
                        replaces = entry['replaces']
                        for replacement in replaces:
                            referenced_member = self.find_member(
                                replacement['name'])
                            del replacement['name']
                            replacement['member'] = referenced_member.uuid
                        member.set_replaces(replaces)
            self._members_fn_ln = {normalize_str(
                f'{member.last_name} {member.first_name}'): member for member in self.members}

        return self.members
