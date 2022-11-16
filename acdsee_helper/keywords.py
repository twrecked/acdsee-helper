import io
import pprint

from .color import color

pp = pprint.PrettyPrinter(indent=4)

""" Formats
We store and manipulate the keywords in several format.

- yaml; as returned from the YAML parser, this comes from the config file
- acdsee; a tab separated list, this comes from the exported keyword file
- dictionary; as a dictionary with None for empty branches, we build this from
  the previous entries
- keywords: list of '|' symbol separated hierarchical keywords, we build this from
  the dictionary
"""


def _hash_to_acdsee(acdsee, hash, depth):
    for topic, value in hash.items():
        acdsee.append(('\t' * depth) + topic)
        if value is not None:
            _hash_to_acdsee(acdsee, value, depth + 1)


def _hash_to_keywords(keywords, hash, base):
    for topic, value in hash.items():
        if value is not None:
            _hash_to_keywords(keywords, value, base + [topic])
        else:
            keywords.add('|'.join(base + [topic]))


def keywords_to_hash(keywords):
    acdsee = {}
    keywords = list(set(keywords))
    keywords.sort()
    for keyword in keywords:
        current_hash = acdsee
        topics = keyword.split('|')
        for index in range(len(topics)):
            topic = topics[index]
            if index == len(topics) - 1:
                if topic not in current_hash:
                    current_hash[topic] = None
            else:
                if topic in current_hash:
                    if type(current_hash[topic]) != dict:
                        current_hash[topic] = {}
                else:
                    current_hash[topic] = {}
                current_hash = current_hash[topic]
    return acdsee


def hash_to_keywords(hash):
    keywords = set()
    _hash_to_keywords(keywords, hash, [])
    return keywords


def hash_to_acdsee(hash):
    acdsee = []
    _hash_to_acdsee(acdsee, hash, 0)
    return acdsee


def hash_to_acsdee_file(hash, file):
    acdsee = "\n".join(hash_to_acdsee(hash))
    with io.open(file, 'w', newline='\r\n') as afile:
        afile.writelines(acdsee)


def acdsee_to_hash(lines, depth=0):
    entries = {}

    # Loop until we detect a return to a previous level, or we run out of lines.
    last = None
    while len(lines) > 0:
        line = lines[0]
        sline = line.strip()
        new_depth = len(line) - len(sline) - 1

        # Going down a level. Update last entry in array to the return value.
        if new_depth > depth:
            entries[last] = acdsee_to_hash(lines, depth + 1)

        # At current level. Add in the end of entries and save value, just
        # incase we have to drop down a level.
        elif new_depth == depth:
            entries[sline] = None
            last = sline
            lines.pop(0)

        # Previous level. Return what we have.
        elif new_depth < depth:
            return entries

    # Ran out of lines. Return what we have.
    return entries


def acdsee_file_to_hash(file, topic=None):
    with open(file, 'r') as keyword_file:
        lines = keyword_file.readlines()
    keywords = acdsee_to_hash(lines)
    if topic is None:
        return keywords
    if topic in keywords:
        return keywords[topic]
    print(color(f'no "{topic}" section detected', fg='red'))
    return None


def yaml_to_hash(entries):
    khash = {}
    for entry in entries:
        if type(entry) is dict:
            for topic, value in entry.items():
                khash[topic] = yaml_to_hash(value)
        else:
            khash[entry] = None
    return khash
