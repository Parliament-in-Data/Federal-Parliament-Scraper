import json
import requests
from bs4 import BeautifulSoup
from member import Member
from meeting import Meeting
import json
from os import path, makedirs
import functools
from util import normalize_str


def member_to_URI(base_path, base_URI, member):
    return member.dump_json(base_path, base_URI)


def meeting_to_URI(base_path, base_URI, meeting):
    return meeting.dump_json(base_path, base_URI)


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

    def dump_json(self, output_path: str, base_URI="/"):
        import concurrent.futures

        self.get_members()
        self.get_plenary_meetings()

        base_path = path.join(output_path, "sessions", f'{self.session}')
        base_URI = f'{base_URI}sessions/{self.session}/'
        makedirs(base_path, exist_ok=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            meeting_URIs = list(executor.map(functools.partial(
                meeting_to_URI, base_path, base_URI), self.plenary_meetings))
            members_URIs = list(executor.map(functools.partial(
                member_to_URI, base_path, base_URI), self.members))

        makedirs(path.join(base_path, "legislation"), exist_ok=True)
        makedirs(path.join(base_path, "questions"), exist_ok=True)

        with open(path.join(base_path, 'legislation', 'unfolded.json'), 'w') as fp:
            json.dump(
                {
                    document.document_number: document.json_representation(base_URI)
                    for document in self.documents.values()
                },
                fp
            )

        with open(path.join(base_path, 'legislation', 'index.json'), 'w') as fp:
            json.dump({document.document_number: f'{base_URI}{document.uri()}' for document in self.documents.values()}, fp)

        with open(path.join(base_path, 'questions', 'index.json'), 'w') as fp:
            json.dump({question.document_number: f'{base_URI}{question.uri()}' for question in self.questions.values()}, fp)

        with open(path.join(base_path, 'session.json'), 'w') as fp:
            json.dump({
                'id': self.session,
                'start': self.start,
                'end': self.end,
                'members': members_URIs,
                'legislation': f'{base_URI}legislation/index.json',
                'questions': f'{base_URI}questions/index.json',
                'meetings': {'plenary': meeting_URIs}}, fp)
        return path.join(base_URI, 'session.json')

    def __init__(self, session: int):
        """Initialize a new instance of the scraper

        Args:
            session (int): Specify the session for which the scraper should be constructed
        Note:
            Only sessions 55 to 52 are supported for now.
        """
        assert (session < 56 and session >
                51), 'Only sessions 52-55 are available via this API'
        self.session = session
        self.plenary_meetings = []
        self.members_dict = {}
        self.questions = {}
        self.documents = {}
        self.members = []
        self.start = ParliamentarySession.sessions[session]['from']
        self.end = ParliamentarySession.sessions[session]['to']
        self._members_fn_ln = {}
        self._members_ln_fn = {}
        # TODO: remove
        self.undefined_members = set()

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
            if member.hasName(query):
                return member
        print("Undefined member: %s" % query)
        self.undefined_members.add(query)

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
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, 'html.parser')
            meetings = soup.find_all('tr')

            self.plenary_meetings = []

            for meeting in meetings:
                self.plenary_meetings.append(Meeting.from_soup(meeting, self))

        return self.plenary_meetings

    def get_members(self):
        """Get all known parliament members within this session

        Returns:
            list(Member): list of all known members within the session
        """
        if not self.members:
            with open('data/composition/%d.json' % self.session) as json_file:
                data = json.load(json_file)
                for entry in data:
                    # TODO: member should probably take entry at construction time instaed of using these setters
                    member = Member(entry['first_name'], entry['last_name'], entry['party'],
                                    entry['province'], entry['language'], entry['wiki'])
                    if 'alternative_names' in entry:
                        member.set_alternative_names(
                            entry['alternative_names'])
                    member.set_gender(entry['gender'])
                    member.set_date_of_birth(entry['date_of_birth'])
                    if 'photo_url' in entry:
                        member.set_photo_url(entry['photo_url'])
                    self.members.append(member)
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
