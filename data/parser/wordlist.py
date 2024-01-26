import re
import os

def load_wordlist(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

def parse(text):
    wordlist_path = os.path.join(os.path.dirname(__file__), 'wordlist.txt')
    wordlist = load_wordlist(wordlist_path)

    # Create a regex pattern that matches any word in the wordlist
    pattern = r'\b(' + '|'.join(re.escape(word) for word in wordlist) + r')\b'
    
    matches = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        matched_word = match.group()
        start_pos, end_pos = match.span()
        matches.append((matched_word, start_pos, end_pos))

    return matches

