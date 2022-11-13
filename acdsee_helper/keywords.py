import io

from .color import color


# Format from YAML is an array of hashes/names.

def _keywords_to_yaml(lines, current_depth=0):
    entries = []
    last = None

    # Loop until we detect a return to a previous level, or we run out of lines.
    while len(lines) > 0:
        line = lines[0]
        sline = line.strip()
        depth = len(line) - len(sline) - 1

        # Going down a level. Update last entry in array to the return value.
        if depth > current_depth:
            entries[-1] = {last: _keywords_to_yaml(lines, current_depth + 1)}

        # At current level. Add in the end of entries and save value, just
        # incase we have to drop down a level.
        elif depth == current_depth:
            last = sline
            lines.pop(0)
            entries.append(sline)

        # Previous level. Return what we have.
        elif depth < current_depth:
            return entries

    # Ran out of lines. Return what we have.
    return entries


def _yaml_to_keywords(keywords, depth):
    lines = []
    for keyword in keywords:
        if type(keyword) is dict:
            for sub_keyword in keyword:
                lines.append(('\t' * depth) + sub_keyword)
                lines = lines + _yaml_to_keywords(keyword[sub_keyword], depth + 1)
        else:
            lines.append(('\t' * depth) + keyword)
    return lines


def read_adcsee_keyword_file(file, base_keyword=None):
    with open(file, 'r') as keyword_file:
        lines = keyword_file.readlines()
    keywords = _keywords_to_yaml(lines)
    if base_keyword is None:
        return keywords
    for entry in keywords:
        if type(entry) is dict:
            if base_keyword in entry:
                return entry[base_keyword]
    print(color(f'no "{base_keyword}" section detected', fg='red'))
    return None


def write_adcsee_keyword_file(file, keywords):
    keywords = "\n".join(_yaml_to_keywords(keywords, 0))
    with io.open(file, 'w', newline='\r\n') as kfile:
        kfile.writelines(keywords)
