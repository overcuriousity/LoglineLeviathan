import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('tldextract').setLevel(logging.CRITICAL) 

import tldextract
import re

def parse(text):
    # Regular expression for detecting potential URLs
    url_regex = r'\b(?:https?|ftp):\/\/[^\s]+'
    matches = []

    for url_match in re.finditer(url_regex, text):
        full_url = url_match.group()

        # Use tldextract to validate the domain and suffix
        extracted = tldextract.extract(full_url)

        if extracted.domain and extracted.suffix:
            start_pos, end_pos = url_match.span()
            matches.append((full_url, start_pos, end_pos))

    return matches


