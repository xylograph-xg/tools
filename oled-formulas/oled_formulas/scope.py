"""Metadata admission for the existing OLED corpus."""
import re

OLED_TERM = re.compile(r'\b(?:[A-Z]{0,3}-?OLEDs?|organic\s+(?:light[\s‐‑–-]*emitting|electroluminescent)\s+(?:diodes?|devices?|displays?))\b', re.I)
ORDINARY_WORDS = {'cooled', 'pooled', 'tooled', 'fooled', 'spooled', 'uncooled', 'schooled'}


def oled_candidate(title, abstract):
    text = f'{title or ""} {abstract or ""}'
    for term in OLED_TERM.findall(text):
        if term.casefold() in ORDINARY_WORDS:
            continue
        if (' ' in term or '-' in term or term.endswith(('OLED','OLEDs','OLEDS'))
                or re.search(r'light[ -]?emitting|electroluminescen|organic diode|exciton',text,re.I)):
            return True
    return False


def ordinary_words_only(record):
    title = record.get('title') or ''
    abstract = (record.get('metadata') or {}).get('abstract') or ''
    return bool(OLED_TERM.search(f'{title} {abstract}')) and not oled_candidate(title,abstract)
