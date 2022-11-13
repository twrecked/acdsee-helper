import os
import pprint
import pyexiv2

from .const import CREATOR_TOOL_TAG, KEYWORDS_TAG, LR_SUBJECT_TAG, PERSON_TAG, EVENT_TAG, SUBJECT_TAG
from .color import color
from .util import remove_duplicates, to_list


def acdsee_region_entry(i, entry):
    return f'Xmp.acdsee-rs.Regions/acdsee-rs:RegionList[{i}]/acdsee-rs:{entry}'


class MetaData:
    def __init__(self, config, file_name):
        self._config = config
        self._file_name = file_name
        self._image = pyexiv2.Image(file_name)
        self._data = self._image.read_xmp()
        self._unknowns = set()

        self._old_data = {}
        self._new_data = {}
        for keyword in [LR_SUBJECT_TAG, PERSON_TAG, EVENT_TAG, SUBJECT_TAG]:
            if keyword in self._data:
                self._old_data[keyword] = self._data[keyword]
                self._new_data[keyword] = self._data[keyword]

    def _parse_area(self):
        people = []
        keywords = []
        i = 1
        while acdsee_region_entry(i, 'Type') in self._data:
            if self._data[acdsee_region_entry(i, 'Type')].lower() == 'face':
                name = self._data[acdsee_region_entry(i, 'Name')]
                keyword = self._config.name_to_keywords(name)
                people.append(name)
                if keyword is not None:
                    keywords.append(keyword)
                else:
                    if name not in self._unknowns:
                        self._unknowns.add(name)
                        print(color(f" missing person config for {name}", fg='yellow'))
                    keywords.append(f'{self._config.people_prefix}|{self._config.people_unknown_prefix}|{name}')
            i = i + 1
        return people, keywords

    @property
    def get_creator(self):
        return self._data.get(CREATOR_TOOL_TAG, "Unknown")

    @property
    def get_event(self):
        # Try in keywords field.
        for keyword in self._data.get(KEYWORDS_TAG, []):
            topics = keyword.split('|')
            if topics[0].lower() == self._config.event_prefix.lower():
                return self._config.event_separator.join(to_list(topics[self._config.event_tag_count:]))
        return None

    @property
    def get_people(self):
        people = []
        for keyword in self._data.get(KEYWORDS_TAG, []):
            topics = keyword.split('|')
            if topics[0].lower() == self._config.people_prefix.lower():
                people.append(topics[-1])

        apeople, akeywords = self._parse_area()
        people = remove_duplicates(people + apeople)
        return people

    @property
    def get_keywords(self):
        keywords = self._data.get(KEYWORDS_TAG, [])
        apeople, akeywords = self._parse_area()
        keywords = self._config.remove_hidden(remove_duplicates(keywords + akeywords))
        return keywords

    @property
    def get_subjects(self):
        subjects = []
        for keyword in self.get_keywords:
            subjects.append(keyword.split('|')[-1])
        return remove_duplicates(subjects)

    @property
    def get_unknown_people(self):
        return self._unknowns

    @property
    def needs_update(self):
        return self._old_data != self._new_data

    def set_event(self, new_event):
        if not new_event and self._config.verbose:
            print(color(f" removing {EVENT_TAG}", fg='magenta'))
        self._new_data[EVENT_TAG] = new_event

    def set_keywords(self, new_keywords):
        if not new_keywords and self._config.verbose:
            print(color(f" removing {LR_SUBJECT_TAG}", fg='magenta'))
        self._new_data[LR_SUBJECT_TAG] = new_keywords

    def set_subjects(self, new_subjects):
        if not new_subjects and self._config.verbose:
            print(color(f" removing {SUBJECT_TAG}", fg='magenta'))
        if not new_subjects:
            new_subjects = ""
        self._new_data[SUBJECT_TAG] = new_subjects

    def set_people(self, new_people):
        if not new_people and self._config.verbose:
            print(color(f" removing {PERSON_TAG}", fg='magenta'))
        self._new_data[PERSON_TAG] = new_people

    def write_changes(self, force=False):
        if force or self.needs_update:
            print("would update")

    def tidy_up(self):
        print(color(f"{os.path.basename(self._file_name)}: processing", style='bold', fg='green'))
        if self._config.verbose:
            print(color(f" created by {self.get_creator}", fg='yellow'))

    def dump(self):
        pp = pprint.PrettyPrinter(indent=4)
        print(color("xmp:", fg='green'))
        pp.pprint(self._data)
        print(color("original-data:", fg='green'))
        pp.pprint(self._old_data)
        print(color("new-data:", fg='green'))
        pp.pprint(self._new_data)
        print(color(f"need-uddating: {self.needs_update}", fg='yellow'))
