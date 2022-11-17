from unidecode import unidecode
from geopy.geocoders import GoogleV3
from geopy import distance

from .color import color, vprint, vvprint

GEOCODE_COUNTRY_CODE_TAG = 'country_code'
GEOCODE_LOCATION_TAG = 'location'
GEOCODE_CITY_TAG = 'city'
GEOCODE_COUNTRY_TAG = 'country'
GEOCODE_STATE_TAG = 'state'


class GeoCache:
    def __init__(self, config):
        self._config = config
        self._coalesce = config.geocode_coalesce
        self._cache = {}

    def check(self, new_coords):
        if self._coalesce == 0:
            vvprint(color(" not caching!", fg="yellow"))
            return None

        for cached_coords, details in self._cache.items():
            meters = distance.distance(cached_coords, new_coords).meters
            if meters < self._coalesce:
                vprint(color(" found a GPS entry", fg="green"))
                return details

        return None

    def update(self, new_coords, details):
        self._cache[new_coords] = details


geo_cache_ = None


class NullGeoLocator:
    def _error(self):
        print(color("no geocode device configured", fg='red'))

    def reverse(self, _coords):
        self._error()
        return {}

    def decode_address(self, _raw_location):
        self._error()
        return {}


class GoogleGeoLocator:
    ADDRESS_MAPPING = [
        # Add a mapping if needed...
        # {'countries': ['GB'],
        #  GEOCODE_COUNTRY_TAG: 'administrative_area_level_1',
        #  GEOCODE_STATE_TAG: 'administrative_area_level_2',
        #  GEOCODE_CITY_TAG: 'postal_town',
        #  GEOCODE_LOCATION_TAG: 'route'
        #  },
        {'countries': [],
         GEOCODE_COUNTRY_TAG: 'country',
         GEOCODE_STATE_TAG: 'administrative_area_level_1',
         GEOCODE_CITY_TAG: 'locality',
         GEOCODE_LOCATION_TAG: 'route'
         },
    ]

    def __init__(self, config):
        global geo_cache_
        self._config = config
        self._locator = GoogleV3(self._config.geocode_token)
        if geo_cache_ is None:
            geo_cache_ = GeoCache(config)
        self._cache = geo_cache_

    def reverse(self, coords):
        reverse = self._cache.check(coords)
        if not reverse:
            reverse = self._locator.reverse(coords)
            if reverse:
                self._cache.update(coords, reverse)
        if not reverse:
            print(color('error, missing GEO information', fg='red'))
        return reverse

    def decode_address(self, raw_location):
        address = raw_location['address_components']
        country_code = ""
        for component in address:
            if 'country' in component['types']:
                country_code = component['short_name']
        if country_code == '':
            print(color(f'error, no country found', fg='red'))
            return {}

        mapping = {}
        for mapping in self.ADDRESS_MAPPING:
            if country_code in mapping['countries'] or not mapping['countries']:
                break

        pieces = {GEOCODE_COUNTRY_CODE_TAG: country_code,
                  GEOCODE_COUNTRY_TAG: None,
                  GEOCODE_STATE_TAG: None,
                  GEOCODE_CITY_TAG: None,
                  GEOCODE_LOCATION_TAG: None}
        for piece in mapping:
            for component in address:
                if mapping[piece] in component['types']:
                    pieces[piece] = unidecode(component['long_name'])
                    break

        return pieces

    def get_exif_info(self, coords):
        # TODO look for this in a cache
        raw_location = self.reverse(coords).raw
        if raw_location:
            return self.decode_address(raw_location)
        return {}


def get_locator(config):
    if config.geocode_backend == 'google':
        return GoogleGeoLocator(config)
    return NullGeoLocator()


def unpack_gps(gps):
    multiplier = 1
    if gps.endswith('W') or gps.endswith('S'):
        gps = gps[:-1]
        multiplier = -1
    if gps.endswith('E') or gps.endswith('N'):
        gps = gps[:-1]

    coords = gps.split(',')
    coord = float(coords[0]) + (float(coords[1]) / 60)

    return multiplier * coord
