
import sys
import pprint
import yaml
import fnmatch

from .color import color, disable_color, enable_color, set_verbosity
from . import keywords

pp = pprint.PrettyPrinter(indent=4)


class BaseConfig:
    def __init__(self, name, options):
        self._name = name
        self._options = options
        self._config = {}

    def _setup_output(self):
        set_verbosity(self._options['verbose'])
        if self._options['no_color'] or not sys.stdout.isatty():
            disable_color()
        else:
            enable_color()

    def _load_config(self):
        if self.config_file is not None:
            with open(self.config_file, 'r') as config_file:
                try:
                    self._config = yaml.safe_load(config_file)
                except yaml.YAMLError as exc:
                    print(color(f'failed to read config: {exc}', fg="red"))

    @property
    def name(self):
        return self._name

    @property
    def config_file(self):
        return self._options['config_file']

    @property
    def verbose(self):
        return self._options['verbose'] > 0

    @property
    def very_verbose(self):
        return self._options['verbose'] > 1

    @property
    def dry_run(self):
        return self._options['dry_run']

    @property
    def file_patterns(self):
        return self._config.get('global', {}).get('file-patterns',
                                                  ["*.xmp", "*.tif", "*.tiff", "*.jpg", "*.jpeg", "*.dng"])

    @property
    def excluded_patterns(self):
        return self._config.get('global', {}).get('excluded-patterns', [])

    def is_data_file(self, file):
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file, pattern):
                return True
        return False

    def is_excluded_file(self, file):
        for pattern in self.excluded_patterns:
            if fnmatch.fnmatch(file, pattern):
                return True
        return False

    @property
    def is_recursive(self):
        return self._options.get('recursive', False)

    def dump(self):
        print(color(f"options (for {self.name}):", fg='green'))
        pp.pprint(self._options)
        print(color(f"config (for {self.name}):", fg='green'))
        pp.pprint(self._config)


class ACDSeeConfig(BaseConfig):
    def __init__(self, options):
        super().__init__('acdsee-helper', options)
        self._keyword_hash = {}
        self._people = {}
        self._exclude = []
        self.load()

    def _load_keywords(self):
        if self.keyword_file is not None:
            self._keyword_hash = keywords.acdsee_file_to_hash(self.keyword_file)

    def _load_people(self):
        people = set()
        if 'people' in self._config:
            people = keywords.yaml_to_hash(self._config['people'])
            people = keywords.hash_to_keywords(people)
        if self.people_prefix in self._keyword_hash:
            people.update(keywords.hash_to_keywords(self._keyword_hash[self.people_prefix]))
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

    def load(self):
        self._load_config()
        self._load_keywords()
        self._load_people()
        self._load_exclusions()
        self._setup_output()

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
    def events(self):
        return self._keyword_hash.get(self.event_prefix, {})

    @property
    def event_prefix(self):
        return self._config.get('acdsee', {}).get('event-prefix', 'Events')

    @property
    def event_tag_count(self):
        return self._config.get('acdsee', {}).get('event-tag-count', -1)

    @property
    def event_separator(self):
        return self._config.get('acdsee', {}).get('event-separator', ', ')

    @property
    def people(self):
        return self._people

    @property
    def people_prefix(self):
        return self._config.get('acdsee', {}).get('people-prefix', 'People')

    @property
    def people_unknown_prefix(self):
        return self._config.get('acdsee', {}).get('people-unknown-prefix', 'Unknown')

    @property
    def places(self):
        return self._keyword_hash.get(self.places_prefix, {})

    @property
    def places_prefix(self):
        return self._config.get('acdsee', {}).get('places-prefix', 'Places')

    @property
    def keywords_event_included(self):
        return self._config.get('acdsee', {}).get('keywords-event-included', True)

    @property
    def keywords_people_included(self):
        return self._config.get('acdsee', {}).get('keywords-people-included', True)

    @property
    def keywords_location_included(self):
        return self._config.get('acdsee', {}).get('keywords-location-included', True)

    @property
    def keywords(self):
        return keywords.hash_to_keywords(self._keyword_hash)

    @property
    def keywords_excluded(self):
        return self._config.get('acdsee', {}).get('keywords-excluded', [])

    @property
    def geocode_backend(self):
        return self._config.get('acdsee', {}).get('geocode-backend', [])

    @property
    def geocode_token(self):
        return self._config.get('acdsee', {}).get('geocode-token', [])

    @property
    def geocode_coalesce(self):
        return self._config.get('acdsee', {}).get('geocode-coalesce', 250)

    @property
    def geocode_unidecode(self):
        return self._config.get('acdsee', {}).get('geocode-unidecode', False)

    @property
    def update_delay(self):
        return self._config.get('acdsee', {}).get('update-delay', 5)

    @property
    def keyword_file(self):
        if self._options['keyword_file'] is not None:
            return self._options['keyword_file']
        return self._config.get('acdsee', {}).get('keywords-file', None)

    def is_config_file(self, file):
        return file == self.config_file or file == self.keyword_file

    def dump(self):
        super().dump()
        #  print(color("keywords_:", fg='green'))
        #  pp.pprint(self._keyword_hash)
        #  print(color("people:", fg='green'))
        #  pp.pprint(self._people)
        #  print(color("exclude:", fg='green'))
        #  pp.pprint(self._exclude)


class DxoConfig(BaseConfig):
    def __init__(self, options):
        super().__init__('dxo-helper', options)
        self.load()

    def load(self):
        self._load_config()
        self._setup_output()

    @property
    def fake_dir(self):
        return self._config.get('dxo', {}).get('fake-dir', None)

    @property
    def models(self):
        return self._config.get('dxo', {})
