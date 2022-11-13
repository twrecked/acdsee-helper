import pprint

from . import const
from . import config
from . import keywords
from . import metadata

from .color import color, disable_color

pp = pprint.PrettyPrinter(indent=4)

if __name__ == '__main__':
    c = config.Config()

    for file in c.file_names:
        m = metadata.MetaData(c, file)
        print(color(f"need-uddating: {m.needs_update}", fg='yellow'))
        m.tidy_up()
        print(color(f"need-uddating: {m.needs_update}", fg='yellow'))
        # m.dump()
        # m.write_changes()


    # k = keywords.read_adcsee_keyword_file(c.keyword_file)
    # pp.pprint(k)
    #
    # keywords.write_adcsee_keyword_file("ignored", k)

