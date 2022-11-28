from unidecode import unidecode
from geopy.geocoders import GoogleV3
from geopy import distance

from .color import warn, error, vprint, vvprint

"""Reverse Lookup a set of latitude/longitude coordinates.

If all goes well it will return a dictionary with 5 elements:
    country_code: 2 letter country code, eg CA
    country: Long country name, eg Canada
    state: Long state/province name, eg Ontario
    city: City name, eg Ottawa
    location: A street name, eg Bank St
    
It may be possible for 'location' to be missing. And note, the code returns
`EXIF` agnostic keys.
"""


GEOCODE_COUNTRY_CODE_TAG = 'country_code'
GEOCODE_LOCATION_TAG = 'location'
GEOCODE_CITY_TAG = 'city'
GEOCODE_COUNTRY_TAG = 'country'
GEOCODE_STATE_TAG = 'state'


class GeoCache:
    """Location caching.

    User can set a distance to see if a 'rough' area has been queried before.
    This will prevent too many look-ups from happening.
    """

    def __init__(self, config):
        self._config = config
        self._coalesce = config.geocode_coalesce
        self._cache = {}

    def check(self, new_coords):
        if self._coalesce == 0:
            vvprint("not caching!")
            return None

        for cached_coords, details in self._cache.items():
            meters = distance.distance(cached_coords, new_coords).meters
            if meters < self._coalesce:
                vprint("found a GPS entry")
                return details

        return None

    def update(self, new_coords, details):
        self._cache[new_coords] = details


geo_cache_ = None


class BaseGeoLocator:
    """Base Geo Locator class.

    They all have to provide the `reverse`, `decode_address` class.
    """

    def __init__(self, config, locator):
        self._config = config
        self._locator = locator

        global geo_cache_
        if geo_cache_ is None:
            geo_cache_ = GeoCache(config)
        self._cache = geo_cache_

    def _squash(self, msg):
        """Remove unicode characters.
        This is entirely optional, but I've found a few places near me that
        use accents and don't use accents for the same component. This just
        squashes them into one.

        :param msg: The message to squash.
        :return: Unidecoded message.
        """
        if self._config.geocode_unidecode:
            return unidecode(msg)
        return msg

    def reverse(self, coords):
        reverse = self._cache.check(coords)
        if reverse is None:
            reverse = self._locator.reverse(coords)
            if reverse:
                self._cache.update(coords, reverse)
        if reverse is None:
            warn('error, missing GEO information')
        return reverse

    def decode_address(self, _raw_location):
        return None

    def get_exif_info(self, coords):
        """Reverse look up and decode in one.

        :param coords Coordinates tuple to look for
        :return Place description of None on failure.
        """
        location = self.reverse(coords)
        if location is not None:
            return self.decode_address(location.raw)
        return None


class NullGeoLocator(BaseGeoLocator):
    def __init__(self, config):
        super().__init__(config, None)

    def reverse(self, _coords):
        error("reverse, no geocode device configured")
        return None

    def decode_address(self, _raw_location):
        error("decode, no geocode device configured")
        return None


class GoogleGeoLocator(BaseGeoLocator):
    """The Google version of the GeoLocator.
    """

    ADDRESS_MAPPING = [
        # Add a mapping if needed...
        # {
        #  'countries': ['GB'],
        #  GEOCODE_COUNTRY_TAG: 'administrative_area_level_1',
        #  GEOCODE_STATE_TAG: 'administrative_area_level_2',
        #  GEOCODE_CITY_TAG: 'postal_town',
        #  GEOCODE_LOCATION_TAG: 'route'
        # },
        {'countries': [],
         GEOCODE_COUNTRY_TAG: 'country',
         GEOCODE_STATE_TAG: 'administrative_area_level_1',
         GEOCODE_CITY_TAG: 'locality',
         GEOCODE_LOCATION_TAG: 'route'
         },
    ]

    def __init__(self, config):
        super().__init__(config, GoogleV3(config.geocode_token))

    def decode_address(self, raw_location):

        # Decode the location and check it looks somewhat sane, in that is has a
        # country code.
        address = raw_location['address_components']
        country_code = ""
        for component in address:
            if 'country' in component['types']:
                country_code = component['short_name']
        if country_code == '':
            error(f'error, no country found')
            return None

        # Pick the handler to map geolocator to the components we are interested
        # in.
        mapping = {}
        for mapping in self.ADDRESS_MAPPING:
            if country_code in mapping['countries'] or not mapping['countries']:
                break

        # Extract the components. We make unreturned components None.
        pieces = {GEOCODE_COUNTRY_CODE_TAG: country_code,
                  GEOCODE_COUNTRY_TAG: None,
                  GEOCODE_STATE_TAG: None,
                  GEOCODE_CITY_TAG: None,
                  GEOCODE_LOCATION_TAG: None}
        for piece in mapping:
            for component in address:
                if mapping[piece] in component['types']:
                    pieces[piece] = self._squash(component['long_name'])
                    break

        return pieces


def get_locator(config):
    """Get Locator determined byu config.

    We currently on support Google.
    """
    if config.geocode_backend == 'google':
        return GoogleGeoLocator(config)
    return NullGeoLocator(config)


def unpack_gps(gps):
    """Convert EXIF coordinates into GeoLocator compatible ones.
    """
    multiplier = 1
    if gps.endswith('W') or gps.endswith('S'):
        gps = gps[:-1]
        multiplier = -1
    if gps.endswith('E') or gps.endswith('N'):
        gps = gps[:-1]

    coords = gps.split(',')
    coord = float(coords[0]) + (float(coords[1]) / 60)

    return multiplier * coord
