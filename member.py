import requests
from bs4 import BeautifulSoup
from util import normalize_str

class Member:
    """
    Class representing a single member of the parliament
    """
    def __init__(self, first_name, last_name, party, province, language, url=None):
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
        self.url = url
    def __repr__(self):
        return "Member(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (self.first_name, self.last_name, self.party, self.province, self.language, self.url)
    def __str__(self):
        return "%s, %s" % (self.first_name, self.last_name)
    def hasName(self, query):
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
    def set_alternative_names(self, names):
        """Set alternative names by which the member should also
        be recognized in the meeting notes.

        Args:
            names (list(str)): All the alternative names of the member
        """
        self.alternative_names = names
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
