import pprint

from . import const
from . import config
from . import keywords
from . import metadata
from . import geocode

from .color import color, disable_color

pp = pprint.PrettyPrinter(indent=4)

if __name__ == '__main__':
    c = config.Config()

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        m.tidy_up()
        # m.dump()
        # m.write_changes()


    # k = keywords.read_adcsee_keyword_file(c.keyword_file)
    # pp.pprint(k)
    #
    # keywords.write_adcsee_keyword_file("ignored", k)

    locator = geocode.get_locator()
    pp.pprint(locator.get_exif_info((27.218010289369108, -82.4555909962064)))
    pp.pprint(locator.get_exif_info(( 53.00504349607705, -2.3400134355823763)))

