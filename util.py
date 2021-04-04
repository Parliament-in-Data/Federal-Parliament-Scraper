import unicodedata
from bs4 import NavigableString
from typing import List


def normalize_str(text: str):
    """Replace diacritical characters and normalize the string this way.

    Args:
        text (str): String to be normalized

    Returns:
        str: Normalized version of the string
    """
    text = clean_string(text.strip())
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')


def clean_string(text: str):
    """Replace MS Office Special Characters from a String as well as double whitespace

    Args:
        text (str):

    Returns:
        str: Cleaned string
    """
    result = ' '.join(text.split())
    result = result.replace('\r', '').replace('.', '').replace(
        '\n', ' ').replace(u'\xa0', u' ').replace(u'\xad', u'-').rstrip().lstrip()
    return result


banned_set = set([
    # No idea about this one, occurs in the dataset but has passed away before the time the dataset was made?
    # Probably another person with the same name but can't find info about them. (see #10)
    ' Ramaekers Jef',
    # Well, the string below was added because of some format issues in https://www.dekamer.be/doc/PCRI/html/52/ip078x.html, we should solve this better (by using a RegEx)
    '(Ingevolge een technisch mankement werd de stemming van mevrouw Inge Vervotte',
    ' afwezig',
    ' opgenomen)',
    '(A la suite d’une erreur technique',
    ' le vote de Mme Inge Vervotte',
    ' absente',
    '(Om technische redenen is er geen stemming nr 2 / Pour raison technique',
    " il n'y a pas de vote n° 2)",
    '(De heer Guido De Padt heeft gestemd vanop de bank van de heer Ludo Van Campenhout',
    ' afwezig)',
    ' a été enregistré)'
    # Dataset error
    #'Vote nominatif - Naamstemming: 002'
])


def clean_list(list: List[any]):
    """Removes falsy items from a list
    """
    return [clean_string(item) for item in list if item and item not in banned_set]


def go_to_p(tag: NavigableString):
    """Go to the nearest parent p tag of a NavigableString.
    """
    while tag.name != "p":
        tag = tag.parent
    return tag
