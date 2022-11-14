import pprint

from geopy.geocoders import GoogleV3

from .color import color

GEOCODE_COUNTRY_CODE_TAG = 'country_code'
GEOCODE_LOCATION_TAG = 'location'
GEOCODE_CITY_TAG = 'city'
GEOCODE_COUNTRY_TAG = 'country'
GEOCODE_STATE_TAG = 'state'


class NullGeoLocator:
    def _error(self):
        print(color("no geocode device configured", fg='red'))

    def reverse(self, coords):
        self._error()
        return {}

    def decode_address(self, raw_location):
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
        self._config = config
        self._locator = GoogleV3(self._config.geocode_token)

    def reverse(self, coords):
        reverse = self._locator.reverse(coords)
        if not reverse:
            print(color('error, missing a piece off GEO information', fg='red'))
        return reverse

    def decode_address(self, raw_location):
        address = raw_location['address_components']
        country_code = ""
        for component in address:
            if 'country' in component['types']:
                country_code = component['short_name']

        mapping = {}
        for mapping in self.ADDRESS_MAPPING:
            if country_code in mapping['countries'] or not mapping['countries']:
                break

        pieces = {GEOCODE_COUNTRY_CODE_TAG: country_code}
        for piece in mapping:
            for component in address:
                if mapping[piece] in component['types']:
                    pieces[piece] = component['long_name']
                    break

        # Make sure it looks sane.
        if len(pieces) != 5:
            print(color(f'error, missing a piece of GEO information {len(pieces)}', fg='red'))
            return {}
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


