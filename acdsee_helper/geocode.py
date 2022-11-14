
from geopy.geocoders import GoogleV3

from .color import color


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
        #  'country': 'administrative_area_level_1',
        #  'state': 'administrative_area_level_2',
        #  'city': 'postal_town',
        #  'location': 'route'
        #  },
        {'countries': [],
         'country': 'country',
         'state': 'administrative_area_level_1',
         'city': 'locality',
         'location': 'route'
         },
    ]

    def __init__(self, api_key):
        self._locator = GoogleV3(api_key)

    def reverse(self, coords):
        return self._locator.reverse(coords)

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

        pieces = {'country_code': country_code}
        for piece in mapping:
            for component in address:
                if mapping[piece] in component['types']:
                    pieces[piece] = component['long_name']
                    break

        return pieces

    def get_exif_info(self, coords):
        raw_location = self.reverse(coords).raw
        if raw_location:
            return self.decode_address(raw_location)
        return {}


def get_locator(config):
    if config.geocode_backend == 'google':
        return GoogleGeoLocator(api_key="AIzaSyDLf6VaaZ2qzD7aQUeE4SHKpJICyWru3Sc")
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


