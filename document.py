from bs4 import BeautifulSoup
import requests
import dateparser
#from activity import LegislativeActivity, QuestionActivity
import re
import json
from util import normalize_str
from os import path
from models import ParliamentaryDocument, ParliamentaryQuestion


MAX_RETRIES = 5


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

def parliamentary_document_from_nr(session, document_nr, retry=0):
    description_uri = f'https://www.dekamer.be/kvvcr/showpage.cfm?section=/flwb&language=nl&cfm=/site/wwwcfm/flwb/flwbn.cfm?lang=N&legislat={session.session}&dossierID={document_nr}'
    page = session.requests_session.get(description_uri)
    soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
    content = soup.find('div', {'id': 'Story'})

    if not content or "not found" in content.get_text():
        return
    if "Er heeft zich een fout voorgedaan" in content.get_text():
        if retry >= MAX_RETRIES:
            print('Gave up on', description_uri)
            return
        else:
            return parliamentary_document_from_nr(session, document_nr, retry=retry + 1)

    date = None
    descriptor = []
    keywords = []
    title = None
    authors = []

    proposal_date = soup.find('td', text=re.compile('Indieningsdatum'))
    if not proposal_date:
        proposal_date = soup.find('td', text=re.compile('[0-9]+/[0-9]+/[0-9]+'))
        if proposal_date:
            date = dateparser.parse(proposal_date.get_text(), languages=['nl'])
    else:
        date = dateparser.parse(
            proposal_date.parent.find_all('td')[-1].get_text(), languages=['nl'])
    descriptor_element = soup.find('td', text=re.compile('Eurovoc-hoofddescriptor'))
    if descriptor_element:
        descriptor = descriptor_element.parent.find_all('td')[-1].get_text().split(' | ')
    keywords_element = soup.find('td', text=re.compile('Eurovoc descriptoren'))
    if keywords_element:
        keywords = keywords_element.parent.find_all('td')[-1].get_text().split(' | ')
    title_element = content.find('h4')
    if title_element:
        title = title_element.get_text().strip()
    doc_type_row = [tag for tag in soup.find_all(
        'td', {'class': "td1x"}) if 'Document type' in tag.get_text()]
    document_type = doc_type_row[0].parent.find(
        'td', {'class': 'td0x'}).find_all(text=True)[0][3:]
    authors_element = [tag for tag in soup.find_all(
        'td', {'class': "td1x"}) if 'Auteur(s)' in tag.get_text()]
    if authors_element:
        authors_element = authors_element[0].parent.find('td', {'class': 'td0x'}).find_all(text=True)
        authors_element = [text.strip() for text in authors_element if (not str(text).isspace()) and ', ' in text]
        for name in authors_element:
            name = normalize_str(name).decode()
            if name in session.get_members_dict():
                authors.append(session.get_members_dict()[name])
            elif extract_name(name) in session.get_members_dict():
                authors.append(session.get_members_dict()[extract_name(name)])
            else:
                print("D:" + name)
    
    return ParliamentaryDocument(document_nr, document_type, title, description_uri, date, descriptor, keywords, authors)

def parliamentary_question_from_nr(session, document_nr, retry=0):
    description_uri = f'https://www.dekamer.be/kvvcr/showpage.cfm?section=inqo&language=nl&cfm=inqoXml.cfm?db=INQO&legislat={session.session}&dossierID=Q{document_nr}'
    page = session.requests_session.get(description_uri)
    soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
    body = soup.find('body')
    if not body or "does not exist" in body.get_text():
        return
    if not body or "Er heeft zich een fout voorgedaan" in body.get_text():
        if retry >= 10:
            print('Gave up on', description_uri)
            return
        else:
            return parliamentary_question_from_nr(session, document_nr, retry=retry + 1)

    date = None
    title = None
    authors = []
    responding_minister = None
    responding_department = None

    authors_element = [tag for tag in soup.find_all('td') if 'Auteur(s)' in tag.get_text()]
    if authors_element:
        authors_element = authors_element[0].parent.find_all('td')[1].get_text().split('\n')
        authors_element = [','.join(text.strip().split(',')[:-1]) for text in authors_element if (not str(text).isspace()) and ', ' in text]

        for name in authors_element:
            name = normalize_str(name).decode()
            if name in session.get_members_dict():
                authors.append(session.get_members_dict()[name])
            elif extract_name(name) in session.get_members_dict():
                authors.append(session.get_members_dict()[extract_name(name)])
            else:
                print("Q:" + name)

    responding_minister_cell = soup.find('i', text=re.compile('Antwoordende minister'))
    if responding_minister_cell:
        responding_minister = responding_minister_cell.find_parent('tr').find_all('td')[1].get_text().strip()[:-1]
        responding_department = responding_minister_cell.find_parent('tr').find_next('tr').get_text().strip()
    
    title_element = soup.find('i', text=re.compile('Titel'))
    if title_element:
        title = title_element.find_parent('tr').find_all('td')[1].get_text().strip()
        title = "\n".join(item.strip()
                                for item in title.split('\n') if item.strip())
    date_element = soup.find('i', text=re.compile('Datum bespreking'))
    if date_element:
        date = dateparser.parse(
                date_element.find_parent('tr').find_all('td')[1].get_text().strip(), languages=['nl'])

    return ParliamentaryQuestion(document_nr, title, description_uri, date, responding_minister, responding_department, authors)
