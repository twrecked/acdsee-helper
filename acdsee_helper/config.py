
import pprint
import yaml
import fnmatch
import argparse

from .color import color, disable_color, enable_color
from . import keywords

pp = pprint.PrettyPrinter(indent=4)


class Config:
    def __init__(self):
        self._args = None
        self._config = {}
        self._people = {}
        self._exclude = []
        self.load()

    def _load_args(self):
        parser = argparse.ArgumentParser(prog="acdsee_helper")
        parser.add_argument("-b", "--base", action="store",
                            help="base directory to monitor")
        parser.add_argument("-c", "--config-file", action="store",
                            help="config file to use")
        parser.add_argument("-d", "--dry-run", action="store_true",
                            help="don't really do any work")
        parser.add_argument("-k", "--keywords-file", action="store",
                            help="ACDSee exported keywords file to read")
        parser.add_argument("-n", "--no-color", action="store_true",
                            help="don't use colours")
        parser.add_argument("-v", "--verbose", action="count", default=0,
                            help="turn on more output")
        parser.add_argument("-p", "--dump-people", action="store_true",
                            help="do nothing, just dump people")
        parser.add_argument("-x", "--dump-xmp", action="store_true",
                            help="do nothing, just dump xmp of file")
        parser.add_argument("-C", "--check-keywords", action="store_true",
                            help="check keywords in file against configued ones")
        parser.add_argument("filename", nargs="*",
                            help="files to update, no files enters watching mode")
        self._args = parser.parse_args()

    def _load_config(self):
        if self.config_file is not None:
            print(color("loading config", fg='yellow'))
            with open(self.config_file, 'r') as config_file:
                try:
                    self._config = yaml.safe_load(config_file)
                except yaml.YAMLError as exc:
                    print(color(f'failed to read config: {exc}', fg="red"))

    def _load_keywords(self):
        if self.keyword_file is not None:
            self._acdsee = keywords.acdsee_file_to_hash(self.keyword_file)

    def _load_people(self):
        people = {}
        if 'people' in self._config:
            people = keywords.yaml_to_hash(self._config['people'])
            people = keywords.hash_to_keywords(people)
        if self.people_prefix in self._acdsee:
            people.update(keywords.hash_to_keywords(self._acdsee[self.people_prefix]))
        self._build_people_map(people)

    def _load_exclusions(self):
        if not self.keywords_event_included:
            self._exclude.append(f'{self.event_prefix}|*')
        if not self.keywords_people_included:
            self._exclude.append(f'{self.people_prefix}|*')
        for exclude in self.keywords_excluded:
            self._exclude.append(f'{exclude}*')

    def _build_people_map(self, entries):
        for entry in entries:
            topics = entry.split('|')
            self._people[topics[-1].lower()] = f'{self.people_prefix}|{entry}'

    def _setup_colors(self):
        if self._args.no_color:
            disable_color()
        else:
            enable_color()

    def load(self):
        self._load_args()
        self._load_config()
        self._load_keywords()
        self._load_people()
        self._load_exclusions()
        self._setup_colors()

    def name_to_keywords(self, name):
        return self._people.get(name.lower(), None)

    def remove_hidden(self, all_keywords):
        keywords = []
        for keyword in all_keywords:
            add = True
            for pattern in self._exclude:
                if fnmatch.fnmatch(keyword, pattern):
                    add = False
                    break
            if add:
                keywords.append(keyword)
        return keywords

    @property
    def mode(self):
        if self._args.dump_xmp:
            return "dump"
        if self._args.check_keywords:
            return "check-keywords"
        return "fix"

    @property
    def verbose(self):
        return self._args.verbose > 0

    @property
    def very_verbose(self):
        return self._args.verbose > 1

    @property
    def dry_run(self):
        return self._args.dry_run

    @property
    def base_directory(self):
        return self._args.base

    @property
    def event_prefix(self):
        return self._config.get('global', {}).get('event-prefix', 'Events')

    @property
    def event_tag_count(self):
        return self._config.get('global', {}).get('event-tag-count', -1)

    @property
    def event_separator(self):
        return self._config.get('global', {}).get('event-separator', ', ')

    @property
    def people_prefix(self):
        return self._config.get('global', {}).get('people-prefix', 'People')

    @property
    def places_prefix(self):
        return self._config.get('global', {}).get('places-prefix', 'Places')

    @property
    def people_unknown_prefix(self):
        return self._config.get('global', {}).get('people-unknown-prefix', 'Unknown')

    @property
    def keywords_event_included(self):
        return self._config.get('global', {}).get('keywords-event-included', True)

    @property
    def keywords_people_included(self):
        return self._config.get('global', {}).get('keywords-people-included', True)

    @property
    def keywords_location_included(self):
        return self._config.get('global', {}).get('keywords-location-included', True)

    @property
    def keywords_excluded(self):
        return self._config.get('global', {}).get('keywords-excluded', [])

    @property
    def geocode_backend(self):
        return self._config.get('global', {}).get('geocode-backend', [])

    @property
    def geocode_token(self):
        return self._config.get('global', {}).get('geocode-token', [])

    @property
    def geocode_coalesce(self):
        return self._config.get('global', {}).get('geocode-coalesce', 250)

    @property
    def update_delay(self):
        return self._config.get('global', {}).get('update-delay', 5)

    @property
    def file_names(self):
        return self._args.filename

    @property
    def file_patterns(self):
        return self._config.get('global', {}).get('file-patterns',
                                                  ["*.xmp", "*.tif", "*.tiff", "*.jpg", "*.jpeg"])

    @property
    def config_file(self):
        return self._args.config_file

    @property
    def keyword_file(self):
        if self._args.keywords_file is not None:
            return self._args.keywords_file
        return self._config.get('global', {}).get('keywords-file', None)

    def is_data_file(self, file):
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file, pattern):
                return True
        return False

    def is_config_file(self, file):
        return file == self.config_file or file == self.keyword_file

    def dump(self):
        print(color("config:", fg='green'))
        pp.pprint(self._config)
        print(color("keywords_:", fg='green'))
        pp.pprint(self._acdsee)
        print(color("people:", fg='green'))
        pp.pprint(self._people)
        print(color("exclude:", fg='green'))
        pp.pprint(self._exclude)

