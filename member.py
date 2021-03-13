import requests
from bs4 import BeautifulSoup
from util import normalize_str
import json
import uuid
from os import path, makedirs
import hashlib
from typing import List

class Member:
    """
    Class representing a single member of the parliament
    """
    def __init__(self, first_name: str, last_name: str, party: str, province: str, language: str, url: str=None):
        """Class representing a single member of the parliament

        Args:
            first_name (str): First name of the member
            last_name (str): Last name of the member
            party (str): Party affiliation of the member
            province (str): Province the member ran in
            language (str): Language of the member
            url (str, optional): URL to the wikipedia page of the member. Defaults to None.
        """
        self.first_name = first_name
        self.last_name = last_name
        self.party = party
        self.province = province
        self.language = language
        self.alternative_names = []
        self.replaces = None
        self.url = url
        sha_1 = hashlib.sha1()
        sha_1.update(self.first_name.encode('utf-8') + self.last_name.encode('utf-8') + self.party.encode('utf-8') + self.province.encode('utf-8'))
        self.uuid = sha_1.hexdigest()[:10]# Should be sufficiently random

    def dump_json(self, base_path: str, base_URI="/"):
        base_path = path.join(base_path, "members")
        base_URI = f'{base_URI}members/'
        resource_name = f'{self.uuid}.json'

        makedirs(base_path, exist_ok=True)

        with open(path.join(base_path, resource_name), 'w+') as fp:
            replaces = list(map(lambda replacement: {'member': f'{base_URI}{replacement["member"]}.json', 'dates': replacement['dates']}, self.replaces))
            json.dump({'id': str(self.uuid), 'first_name': self.first_name, 'last_name': self.last_name, 'language': self.language, 'province': self.province, 'party': self.party, 'wiki': self.url, 'replaces': replaces}, fp, ensure_ascii=False)

        return f'{base_URI}{resource_name}'
    def __repr__(self):
        return "Member(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (self.first_name, self.last_name, self.party, self.province, self.language, self.url)
    def __str__(self):
        return "%s, %s" % (self.first_name, self.last_name)
    def hasName(self, query: str):
        """Compare the query string with the "{last_name} {first_name}" combination of
        this member, ignoring any diactritical characters. Alternative names are also possible for
        the member, this is sometimes necessary.

        Args:
            query (str): Name as seen in the meeting notes of the parliament.

        Returns:
            bool: Is this the name of this member
        """
        name = "%s %s" % (self.last_name, self.first_name)
        # Fallback for alternative names
        if self.alternative_names:
            for n in self.alternative_names:
                if normalize_str(query) == normalize_str(n):
                    return True
        return normalize_str(query) == normalize_str(name)
    def set_alternative_names(self, names: List[str]):
        """Set alternative names by which the member should also
        be recognized in the meeting notes.

        Args:
            names (list(str)): All the alternative names of the member
        """
        self.alternative_names = names
    def set_replaces(self, replaces: List[any]):
        """Set which members are replaces when by this member.

        Args:
            replaces (list): All the timespans a member was replaced
        """
        self.replaces = replaces
    def get_image(self):
        """If the Member has a Wikipedia page, this method will attempt to scrape
        their image from this website.

        Returns:
            str: URI to the image or None if no image was found.
        """
        if not self.url:
            return None
        page = requests.get(self.url)

        soup = BeautifulSoup(page.content, 'html.parser')
        result = None
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            result = "https:%s" % infobox.find('img')['src'] if infobox.find('img') else None
        return result
