from bs4 import BeautifulSoup
import parliament_parser
import requests
import dateparser
from activity import LegislativeActivity, QuestionActivity
import re
import json
from util import normalize_str
from os import path


def extract_name(name: str):
    match = re.match(r"(.+, .+) (\S+)$", name)
    if match and match.group(1):
        res = match.group(1)
        res = res.replace(' CD&V -', '') # Fixes a bug caused by "het kartel"
        if res[-1] == ',':
            res = res[:-1]
        return res
    else:
        return name


class ParliamentaryDocument:
    def __init__(self, session, document_number):
        self.session = session
        self.document_number = document_number
        self.descriptor = None
        self.keywords = None
        self.title = None
        self.document_type = None
        self.date = dateparser.parse(session.start)
        self.authors = []
        self._initialize()
        self.session.documents[document_number] = self
        self._register_activities()

    def description_uri(self):
        return f'https://www.dekamer.be/kvvcr/showpage.cfm?section=/flwb&language=nl&cfm=/site/wwwcfm/flwb/flwbn.cfm?lang=N&legislat={self.session.session}&dossierID={self.document_number}'

    def uri(self):
        return f'legislation/{self.document_number}.json'

    def json_representation(self, base_URI="/"):
        result = {}
        result['document_number'] = self.document_number
        if self.document_type:
            result['document_type'] = self.document_type
        if self.title:
            result['title'] = self.title
        result['source'] = self.description_uri()
        if not self.date:
            self.date = dateparser.parse(self.session.start)
        result['date'] = self.date.isoformat()
        result['authors'] = [
            f'{base_URI}{author.uri()}' for author in self.authors]
        if self.descriptor:
            result['descriptor'] = self.descriptor
        if self.keywords:
            result['keywords'] = self.keywords
        return result

    def json(self, base_path, base_URI="/"):
        base_path = path.join(base_path, "legislation")
        with open(path.join(base_path, f'{self.document_number}.json'), 'w+') as fp:
            json.dump(self.json_representation(base_URI), fp, ensure_ascii=False)
        return f'{base_URI}{self.uri}'

    def _initialize(self, retry=False):
        page = self.session.requests_session.get(self.description_uri())
        soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
        content = soup.find('div', {'id': 'Story'})

        if not content or "not found" in content.get_text() or "Er heeft zich een fout voorgedaan" in content.get_text():
            if retry:
                return
            else:
                self._initialize(retry=True)
                return

        proposal_date = soup.find('td', text=re.compile('Indieningsdatum'))
        if not proposal_date:
            proposal_date = soup.find('td', text=re.compile('[0-9]+/[0-9]+/[0-9]+'))
            if proposal_date:
               self.date = dateparser.parse(proposal_date.get_text(), languages=['nl'])
        else:
            self.date = dateparser.parse(
                proposal_date.parent.find_all('td')[-1].get_text(), languages=['nl'])
        descriptor = soup.find(
            'td', text=re.compile('Eurovoc-hoofddescriptor'))
        if descriptor:
            self.descriptor = descriptor.parent.find_all('td')[-1].get_text().split(' | ')
        keywords = soup.find('td', text=re.compile('Eurovoc descriptoren'))
        if keywords:
            self.keywords = keywords.parent.find_all(
                'td')[-1].get_text().split(' | ')
        title = content.find('h4')
        if title:
            self.title = title.get_text().strip()
        doc_type_row = [tag for tag in soup.find_all(
            'td', {'class': "td1x"}) if 'Document type' in tag.get_text()]
        self.document_type = doc_type_row[0].parent.find(
            'td', {'class': 'td0x'}).find_all(text=True)[0][3:]
        authors = [tag for tag in soup.find_all(
            'td', {'class': "td1x"}) if 'Auteur(s)' in tag.get_text()]
        if authors:
            authors = authors[0].parent.find(
                'td', {'class': 'td0x'}).find_all(text=True)
            authors = [text.strip() for text in authors if (
                not str(text).isspace()) and ', ' in text]
            for name in authors:
                name = normalize_str(name).decode()
                if name in self.session.get_members_dict():
                    self.authors.append(self.session.get_members_dict()[name])
                elif extract_name(name) in self.session.get_members_dict():
                    self.authors.append(self.session.get_members_dict()[
                                        extract_name(name)])
                else:
                    print("D:" + name)

    def _register_activities(self):
        if not self.authors:
            return
        for author in self.authors:
            author.post_activity(LegislativeActivity(author, self.date, self))


class ParliamentaryQuestion:
    def __init__(self, session, document_number: str):
        from datetime import datetime

        self.session = session
        self.document_number = document_number
        self.authors = []
        self.title = None
        self.responding_minister = None
        self.date = dateparser.parse(session.start)
        self._initialize()
        self.session.questions[document_number] = self
        self._register_activities()

    def _register_activities(self):
        if not self.authors:
            return
        for author in self.authors:
            author.post_activity(QuestionActivity(author, self.date, self))

    def uri(self):
        return f'questions/{self.document_number}.json'

    def json_representation(self, base_URI="/"):
        result = {}
        result['document_number'] = self.document_number
        result['title'] = self.title
        if not self.date:
            self.date = dateparser.parse(self.session.start)
        result['date'] = self.date.isoformat()
        result['source'] = self.description_uri()
        if self.responding_minister:
            result['responding_minister'] = self.responding_minister
            result['responding_department'] = self.responding_department
        result['authors'] = [
            f'{base_URI}{author.uri()}' for author in self.authors]
        return result

    def json(self, base_path, base_URI="/"):
        base_path = path.join(base_path, "questions")
        with open(path.join(base_path, f'{self.document_number}.json'), 'w+') as fp:
            json.dump(self.json_representation(base_URI), fp, ensure_ascii=False)
        return f'{base_URI}{self.uri}'

    def description_uri(self):
        return f'https://www.dekamer.be/kvvcr/showpage.cfm?section=inqo&language=nl&cfm=inqoXml.cfm?db=INQO&legislat={self.session.session}&dossierID=Q{self.document_number}'

    def _initialize(self, retry=0):
        page = self.session.requests_session.get(self.description_uri())
        soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
        body = soup.find('body')
        if not body or "does not exist" in body.get_text():
            return
        if not body or "Er heeft zich een fout voorgedaan" in body.get_text():
            if retry >= 10:
                print('Gave up on', self.description_uri())
                return
            else:
                self._initialize(retry=retry + 1)
                return

        authors = [tag for tag in soup.find_all(
            'td') if 'Auteur(s)' in tag.get_text()]
        if authors:
            authors = authors[0].parent.find_all(
                'td')[1].get_text().split('\n')
            authors = [','.join(text.strip().split(
                ',')[:-1]) for text in authors if (not str(text).isspace()) and ', ' in text]

        for name in authors:
            name = normalize_str(name).decode()
            if name in self.session.get_members_dict():
                self.authors.append(self.session.get_members_dict()[name])
            elif extract_name(name) in self.session.get_members_dict():
                self.authors.append(self.session.get_members_dict()[
                                    extract_name(name)])
            else:
                print("Q:" + name)
        responding_minister_cell = soup.find(
            'i', text=re.compile('Antwoordende minister'))
        if responding_minister_cell:
            self.responding_minister = responding_minister_cell.find_parent('tr').find_all('td')[
                1].get_text().strip()[:-1]
            self.responding_department = responding_minister_cell.find_parent('tr').find_next('tr').get_text().strip()
        
        title = soup.find('i', text=re.compile('Titel'))
        if title:
            self.title = title.find_parent('tr').find_all('td')[
                1].get_text().strip()
            self.title = "\n".join(item.strip()
                                   for item in self.title.split('\n') if item.strip())
        date = soup.find('i', text=re.compile('Datum bespreking'))
        if date:
            self.date = dateparser.parse(
                date.find_parent('tr').find_all('td')[1].get_text().strip(), languages=['nl'])
