import pprint
import pyexiv2

from .const import XMP_CREATOR_TOOL_TAG, ACDSEE_KEYWORDS_TAG, LR_SUBJECT_TAG, IPTCEXT_PERSON_TAG, IPTCEXT_EVENT_TAG, \
    DC_SUBJECT_TAG, EXIF_GPS_LATITUDE_TAG, EXIF_GPS_LONGITUDE_TAG, PS_GEO_CITY_TAG, PS_GEO_COUNTRY_TAG, \
    IPTC_GEO_COUNTRY_CODE_TAG, IPTC_GEO_LOCATION_TAG, PS_GEO_STATE_TAG, EXIF_MAKE_TAG, EXIF_MODEL_TAG
from .color import info, warn, vprint, vvprint
from .geocode import GEOCODE_COUNTRY_CODE_TAG, GEOCODE_LOCATION_TAG, GEOCODE_CITY_TAG, GEOCODE_COUNTRY_TAG, \
    GEOCODE_STATE_TAG
from .util import remove_duplicates, to_list
from . import geocode


# This is a list of all the tags we might change. We back them into `_old_data`
# and check with `_new_data` to make sure things have really changed.
BACKUP_TAGS = [LR_SUBJECT_TAG, IPTCEXT_PERSON_TAG, IPTCEXT_EVENT_TAG, DC_SUBJECT_TAG, IPTC_GEO_COUNTRY_CODE_TAG,
               IPTC_GEO_LOCATION_TAG, PS_GEO_CITY_TAG, PS_GEO_COUNTRY_TAG, PS_GEO_STATE_TAG]


# Convert `geocode` tags to the EXIF/IPTC/XMP ones we are interested in.
GEO_TAGS_TO_EXIF = {
    GEOCODE_COUNTRY_CODE_TAG: IPTC_GEO_COUNTRY_CODE_TAG,
    GEOCODE_LOCATION_TAG: IPTC_GEO_LOCATION_TAG,
    GEOCODE_CITY_TAG: PS_GEO_CITY_TAG,
    GEOCODE_COUNTRY_TAG: PS_GEO_COUNTRY_TAG,
    GEOCODE_STATE_TAG: PS_GEO_STATE_TAG
}


def acdsee_region_entry(i, entry):
    return f'Xmp.acdsee-rs.Regions/acdsee-rs:RegionList[{i}]/acdsee-rs:{entry}'


def geo_tag_to_exif(tag):
    return GEO_TAGS_TO_EXIF.get(tag, None)


class MetaData:
    def __init__(self, config, file_name):
        self._msg = ''
        self._config = config
        self._file_name = file_name
        self._image = None
        self._unknowns = set()
        self._pp = pprint.PrettyPrinter(indent=4)

        self._image = pyexiv2.Image(file_name)
        self._exif = self._image.read_exif()
        self._data = self._image.read_xmp()
        self._iptc = self._image.read_iptc()

        # Here we copy pieces from the 3 separate sections into a single
        # dictionary.This simplifies the check to see if data has really
        # changed and the code that unpacks the location data - currently
        # location some data is IPTC based and some is XMP based.
        self._old_data = {}
        self._new_data = {}
        for keyword in BACKUP_TAGS:
            if keyword in self._exif:
                self._old_data[keyword] = self._exif[keyword]
                self._new_data[keyword] = self._exif[keyword]
            if keyword in self._data:
                self._old_data[keyword] = self._data[keyword]
                self._new_data[keyword] = self._data[keyword]
            if keyword in self._iptc:
                self._old_data[keyword] = self._iptc[keyword]
                self._new_data[keyword] = self._iptc[keyword]

    def __del__(self):
        if self._image is not None:
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
                        warn(f" missing person config for {name}")
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
        keywords = to_list(self._data.get(ACDSEE_KEYWORDS_TAG, []))
        lkeywords = to_list(self._new_data.get(LR_SUBJECT_TAG, []))
        apeople, akeywords = self._parse_area()
        return remove_duplicates(keywords + lkeywords + akeywords)

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
                vprint(f" removing {IPTCEXT_EVENT_TAG}", fg='magenta')
                self._new_data[IPTCEXT_EVENT_TAG] = None
        else:
            self._new_data[IPTCEXT_EVENT_TAG] = {'lang="x-default"': new_event}

    def set_keywords(self, new_keywords):
        if not new_keywords:
            if LR_SUBJECT_TAG in self._old_data:
                vprint(f" removing {LR_SUBJECT_TAG}", fg='magenta')
                self._new_data[LR_SUBJECT_TAG] = None
        else:
            self._new_data[LR_SUBJECT_TAG] = new_keywords

    def set_subjects(self, new_subjects):
        if not new_subjects:
            if DC_SUBJECT_TAG in self._old_data and self._old_data[DC_SUBJECT_TAG] != ['']:
                vprint(f" removing {DC_SUBJECT_TAG}", fg='magenta')
                self._new_data[DC_SUBJECT_TAG] = ['']
        else:
            self._new_data[DC_SUBJECT_TAG] = new_subjects

    def set_people(self, new_people):
        if not new_people:
            if IPTCEXT_PERSON_TAG in self._old_data:
                vprint(f" removing {IPTCEXT_PERSON_TAG}", fg='magenta')
                self._new_data[IPTCEXT_PERSON_TAG] = None
        else:
            self._new_data[IPTCEXT_PERSON_TAG] = new_people

    def set_make_model(self, make, model):
        self._image.modify_exif({EXIF_MAKE_TAG: make, EXIF_MODEL_TAG: model})

    def fix_up_start(self):
        # info(f"{os.path.basename(self._file_name)}:", style='bold')
        info(f"{self._file_name}:", style='bold')
        self._msg = ''

    def fix_up_finished(self):
        vprint(f"finished{self._msg}", style='bold')

    def fix_up(self):
        info(f" processing tags")
        self.set_event(self.get_event)
        self.set_keywords(self.get_keywords)
        self.set_subjects(self.get_subjects)
        self.set_people(self.get_people)

    def fix_up_geo(self):
        info(f" processing GPS data")
        latitude, longitude = self.get_geo_coords
        if latitude is None or longitude is None:
            self._msg = " (no coords, nothing to do)"
            return

        # Hand it off to the geocoder. Make something useful comes back.
        locator = geocode.get_locator(self._config)
        geo_tags = locator.get_exif_info((latitude, longitude))
        if not geo_tags:
            self._msg = " (couldn't get details)"

        # Convert geocode tags to exif/xmp/iptc tags. Handle empty tags smartly,
        # if it isn't present then don't add an empty entry.
        for tag, value in geo_tags.items():
            exif_tag = geo_tag_to_exif(tag)

            # XXX remove location if not wanted??
            #  I think not having it in the keywords is enough
            # if not self._config.keywords_location_included and tag == 'location':
            #     value = None

            if value is None:
                if exif_tag in self._old_data:
                    if self._old_data[exif_tag] != '':
                        self._new_data[exif_tag] = ''
                        vprint(f'removing {tag}', fg='magenta')
                    else:
                        vprint(f'ignoring blank {tag}', fg='magenta')
                else:
                    vprint(f'ignoring removed {tag}', fg='magenta')
            else:
                self._new_data[exif_tag] = value

        # Build the places keywords.
        keywords = [self._config.places_prefix]
        for tag in ['country', 'state', 'city']:
            if geo_tags.get(tag) is not None:
                keywords.append(geo_tags.get(tag))
        if self._config.keywords_location_included and geo_tags.get('location') is not None:
            keywords.append(geo_tags.get('location'))
        if len(keywords) > 1:
            keyword = "|".join(keywords)
            self.set_keywords(self.get_keywords + [keyword])

    def write_changes(self, force=False):
        if force or self.needs_update:

            # split into exif, xmp and iptc specific changes. As mentioned,
            # this lets us simply places like `fix_up_geo` by not having to worry
            # about where we put the updated tag.
            exif_changes = {}
            xmp_changes = {}
            iptc_changes = {}
            for tag, value in self._new_data.items():
                if tag.lower().startswith('iptc.'):
                    iptc_changes[tag] = value
                elif tag.lower().startswith('xmp.'):
                    xmp_changes[tag] = value
                else:
                    exif_changes[tag] = value
            vvprint(f" from\n{self._pp.pformat(self._old_data)}", fg='cyan')
            vvprint(f" to-exif\n{self._pp.pformat(exif_changes)}", fg='green')
            vvprint(f" to-xmp\n{self._pp.pformat(xmp_changes)}", fg='green')
            vvprint(f" to-iptc\n{self._pp.pformat(iptc_changes)}", fg='green')

            if not self._config.dry_run:
                if iptc_changes:
                    self._image.modify_iptc(iptc_changes)
                if xmp_changes:
                    self._image.modify_xmp(xmp_changes)
                if exif_changes:
                    self._image.modify_exif(exif_changes)
            else:
                self._msg = ' (but only pretending to write)'

            self._old_data = self._new_data
        else:
            vvprint(f" from and to\n{self._pp.pformat(self._old_data)}", fg='cyan')
            self._msg = " (nothing changed, no write done)"

    def dump_xmp(self):
        info("xmp:")
        self._pp.pprint(self._data)

    def dump_exif(self):
        info("exif:")
        self._pp.pprint(self._exif)

    def dump(self):
        self.dump_xmp()
        info("original-data:")
        self._pp.pprint(self._old_data)
        info("new-data:")
        self._pp.pprint(self._new_data)
        info(f"needs-updating: {self.needs_update}")
