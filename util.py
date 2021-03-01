import unicodedata

def normalize_str(text):
    """Replace diacritical characters and normalize the string this way.

    Args:
        text (str): String to be normalized

    Returns:
        str: Normalized version of the string
    """
    text = clean_string(text.strip())
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')

def clean_string(text):
    """Replace MS Office Special Characters from a String as well as double whitespace

    Args:
        text (str):

    Returns:
        str: Cleaned string
    """
    result = ' '.join(text.split())
    result = result.replace('\r', '').replace('\n', ' ').replace(u'\xa0', u' ').replace(u'\xad', u'-').rstrip().lstrip()
    return result

def clean_list(list):
    """Removes falsy items from a list
    """
    return [item for item in list if item]

def go_to_p(tag):
    """Go to the nearest parent p tag of a NavigableString.
    """
    while tag.name != "p":
        tag = tag.parent
    return tag