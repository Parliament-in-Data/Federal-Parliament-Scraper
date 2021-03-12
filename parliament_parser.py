import json
import requests
from bs4 import BeautifulSoup
from member import Member
from meeting import Meeting
import json
from os import path, makedirs


class ParliamentarySession:
    '''
    A ParliamentarySession object is the main entryway to the scraper.
    It is constructed based on the Session one wants to obtain information on.
    From there information can be obtained on the members of the parliament in that session and its meetings.
    '''
    sessions = {
        55: {'from': '20/06/2019', 'to': '19/6/2024'},
        54: {'from': '19/06/2014', 'to': '25/4/2019'},
        53: {'from': '13/06/2010', 'to': '24/4/2014'},
        52: {'from': '10/06/2007', 'to': '6/5/2010'},
    }

    def dump_json(self, output_path: str, base_URI="/"):
        self.get_members()
        self.get_plenary_meetings()

        base_path = path.join(output_path, "sessions", f'{self.session}')
        base_URI = f'{base_URI}sessions/{self.session}/'
        makedirs(base_path, exist_ok=True)

        with open(path.join(base_path, 'session.json'), 'w+') as fp:
            json.dump({
                'id': self.session,
                'start': self.start,
                'end': self.end,
                'members': [member.dump_json(base_path, base_URI) for member in self.members],
                'meetings': {'plenary': [meeting.dump_json(base_path, base_URI) for meeting in self.plenary_meetings]}}, fp)
        return path.join(base_path, 'session.json')
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
        self.members = []
        self.start = ParliamentarySession.sessions[session]['from']
        self.end = ParliamentarySession.sessions[session]['to']

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

        for member in self.members:
            if member.hasName(query):
                return member
        print("Undefined member: %s" % query)
        self.undefined_members.add(query)

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
                    member = Member(entry['first_name'], entry['last_name'], entry['party'],
                                    entry['province'], entry['language'], entry['wiki'])
                    if 'alternative_names' in entry:
                        member.set_alternative_names(
                            entry['alternative_names'])
                    self.members.append(member)
        return self.members
