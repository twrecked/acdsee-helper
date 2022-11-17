import os
import pprint
import pyexiv2

from .const import XMP_CREATOR_TOOL_TAG, ACDSEE_KEYWORDS_TAG, LR_SUBJECT_TAG, IPTCEXT_PERSON_TAG, IPTCEXT_EVENT_TAG, \
    DC_SUBJECT_TAG, EXIF_GPS_LATITUDE_TAG, EXIF_GPS_LONGITUDE_TAG, PS_GEO_CITY_TAG, PS_GEO_COUNTRY_TAG, \
    IPTC_GEO_COUNTRY_CODE_TAG, IPTC_GEO_LOCATION_TAG, PS_GEO_STATE_TAG, EXIF_MAKE_TAG, EXIF_MODEL_TAG
from .color import color, vprint, vvprint
from .util import remove_duplicates, to_list
from . import geocode

BACKUP_TAGS = [LR_SUBJECT_TAG, IPTCEXT_PERSON_TAG, IPTCEXT_EVENT_TAG, DC_SUBJECT_TAG, IPTC_GEO_COUNTRY_CODE_TAG,
               IPTC_GEO_LOCATION_TAG, PS_GEO_CITY_TAG, PS_GEO_COUNTRY_TAG, PS_GEO_STATE_TAG]


def acdsee_region_entry(i, entry):
    return f'Xmp.acdsee-rs.Regions/acdsee-rs:RegionList[{i}]/acdsee-rs:{entry}'


class MetaData:
    def __init__(self, config, file_name):
        self._msg = ''
        self._config = config
        self._file_name = file_name
        self._image = pyexiv2.Image(file_name)
        self._exif = self._image.read_exif()
        self._data = self._image.read_xmp()
        self._unknowns = set()
        self._pp = pprint.PrettyPrinter(indent=4)

        self._old_data = {}
        self._new_data = {}
        for keyword in BACKUP_TAGS:
            if keyword in self._data:
                self._old_data[keyword] = self._data[keyword]
                self._new_data[keyword] = self._data[keyword]

    def __del__(self):
        self._image.close()

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
        return self._data.get(XMP_CREATOR_TOOL_TAG, "Unknown")

    @property
    def get_event(self):
        # Try in keywords field.
        for keyword in self._data.get(ACDSEE_KEYWORDS_TAG, []):
            topics = keyword.split('|')
            if topics[0].lower() == self._config.event_prefix.lower():
                return self._config.event_separator.join(to_list(topics[self._config.event_tag_count:]))
        return None

    @property
    def get_people(self):
        people = []
        for keyword in self._data.get(ACDSEE_KEYWORDS_TAG, []):
            topics = keyword.split('|')
            if topics[0].lower() == self._config.people_prefix.lower():
                people.append(topics[-1])

        apeople, akeywords = self._parse_area()
        people = remove_duplicates(people + apeople)
        return people

    @property
    def get_keywords(self):
        keywords = self._data.get(ACDSEE_KEYWORDS_TAG, [])
        apeople, akeywords = self._parse_area()
        keywords = self._config.remove_hidden(remove_duplicates(keywords + akeywords))
        return keywords

    @property
    def get_all_keywords(self):
        keywords = self._data.get(ACDSEE_KEYWORDS_TAG, [])
        lkeywords = self._new_data.get(LR_SUBJECT_TAG, [])
        apeople, akeywords = self._parse_area()
        keywords = remove_duplicates(keywords + lkeywords + akeywords)
        return keywords

    @property
    def get_subjects(self):
        subjects = []
        for keyword in self.get_keywords:
            subjects.append(keyword.split('|')[-1])
        return remove_duplicates(subjects)

    @property
    def get_geo_coords(self):
        latitude = self._data.get(EXIF_GPS_LATITUDE_TAG, None)
        longitude = self._data.get(EXIF_GPS_LONGITUDE_TAG, None)
        if latitude and longitude:
            return geocode.unpack_gps(latitude), geocode.unpack_gps(longitude)
        return None, None

    @property
    def get_make_model(self):
        return self._exif.get(EXIF_MAKE_TAG, "UNKNOWN"), self._exif.get(EXIF_MODEL_TAG, "UNKNOWN")

    # TODO get_people_keywords
    # TODO get_geo_keyword

    @property
    def get_unknown_people(self):
        return self._unknowns

    @property
    def needs_update(self):
        return self._old_data != self._new_data

    def set_event(self, new_event):
        if not new_event:
            if IPTCEXT_EVENT_TAG in self._old_data:
                vprint(color(f" removing {IPTCEXT_EVENT_TAG}", fg='magenta'))
                self._new_data[IPTCEXT_EVENT_TAG] = None
        else:
            self._new_data[IPTCEXT_EVENT_TAG] = {'lang="x-default"': new_event}

    def set_keywords(self, new_keywords):
        if not new_keywords:
            if LR_SUBJECT_TAG in self._old_data:
                vprint(color(f" removing {LR_SUBJECT_TAG}", fg='magenta'))
                self._new_data[LR_SUBJECT_TAG] = None
        else:
            self._new_data[LR_SUBJECT_TAG] = new_keywords

    def set_subjects(self, new_subjects):
        if not new_subjects:
            if DC_SUBJECT_TAG in self._old_data and self._old_data[DC_SUBJECT_TAG] != ['']:
                vprint(color(f" removing {DC_SUBJECT_TAG}", fg='magenta'))
                self._new_data[DC_SUBJECT_TAG] = ['']
        else:
            self._new_data[DC_SUBJECT_TAG] = new_subjects

    def set_people(self, new_people):
        if not new_people:
            if IPTCEXT_PERSON_TAG in self._old_data:
                vprint(color(f" removing {IPTCEXT_PERSON_TAG}", fg='magenta'))
                self._new_data[IPTCEXT_PERSON_TAG] = None
        else:
            self._new_data[IPTCEXT_PERSON_TAG] = new_people

    def set_make_model(self, make, model):
        self._image.modify_exif({EXIF_MAKE_TAG: make, EXIF_MODEL_TAG: model})

    def fix_up_start(self):
        print(color(f"{os.path.basename(self._file_name)}:", style='bold', fg='green'))
        self._msg = ''

    def fix_up_finished(self):
        vprint(color(f"finished{self._msg}", style='bold', fg='green'))

    def fix_up(self):
        print(color(f" processing tags", fg='green'))

        self.set_event(self.get_event)
        self.set_keywords(self.get_keywords)
        self.set_subjects(self.get_subjects)
        self.set_people(self.get_people)

    def fix_up_geo(self):
        print(color(f" processing GPS data", fg='green'))

        latitude, longitude = self.get_geo_coords
        if latitude and longitude:
            locator = geocode.get_locator(self._config)
            geo_tags = locator.get_exif_info((latitude, longitude))
            if geo_tags:
                self._new_data[IPTC_GEO_COUNTRY_CODE_TAG] = geo_tags['country_code']
                self._new_data[IPTC_GEO_LOCATION_TAG] = geo_tags['location']
                self._new_data[PS_GEO_CITY_TAG] = geo_tags['city']
                self._new_data[PS_GEO_COUNTRY_TAG] = geo_tags['country']
                self._new_data[PS_GEO_STATE_TAG] = geo_tags['state']

                keywords = [self._config.places_prefix]
                for tag in ['country', 'state', 'city']:
                    if geo_tags.get(tag) is not None:
                        keywords.append(geo_tags.get(tag))
                if self._config.keywords_location_included and geo_tags.get('location') is not None:
                    keywords.append(geo_tags.get('location'))
                if len(keywords) > 1:
                    keyword = "|".join(keywords)
                    self.set_keywords(self.get_keywords + [keyword])
            else:
                self._msg = " (couldn't get details)"
        else:
            self._msg = " (no coords, nothing to do)"

    def write_changes(self, force=False):
        if force or self.needs_update:
            vvprint(color(f" from\n{self._pp.pformat(self._old_data)}", fg='cyan'))
            vvprint(color(f" to\n{self._pp.pformat(self._new_data)}", fg='green'))
            if not self._config.dry_run:
                print(color(f" writing changes", fg='green'))
                self._image.modify_xmp(self._new_data)
            else:
                self._msg = ' (but only pretending to write)'

            self._old_data = self._new_data

    def dump_xmp(self):
        print(color("xmp:", fg='green'))
        self._pp.pprint(self._data)

    def dump_exif(self):
        print(color("exif:", fg='green'))
        self._pp.pprint(self._exif)

    def dump(self):
        self.dump_xmp()
        print(color("original-data:", fg='green'))
        self._pp.pprint(self._old_data)
        print(color("new-data:", fg='green'))
        self._pp.pprint(self._new_data)
        print(color(f"needs-updating: {self.needs_update}", fg='yellow'))

    def dump2(self):
        print(self._exif.get("Exif.Image.Model", "UNKNOWN"))
